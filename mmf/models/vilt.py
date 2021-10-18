# Copyright (c) Facebook, Inc. and its affiliates.
import logging
from dataclasses import dataclass, field
from typing import Any, Dict

import torch
from mmf.common.registry import registry
from mmf.models.base_model import BaseModel
from mmf.models.transformers.heads.utils import HeadsDict
from mmf.modules.encoders import TransformerEncoder, ViTEncoder
from mmf.modules.losses import MMFLoss
from mmf.utils.build import build_encoder
from mmf.utils.modeling import get_bert_configured_parameters
from omegaconf import MISSING
from torch import Tensor, nn


logger = logging.getLogger()


class ViLTImageEmbedding(nn.Module):
    """
    Patch embedding used for ViLT.
    https://arxiv.org/pdf/2102.03334.pdf
    Implementation based off
    https://github.com/dandelin/ViLT/blob/master/vilt/modules/vilt_module.py
    Using huggingface ViT modules.
    Can be built with random init or the embeddings weights from an exisiting
    ViT model from huggingface. Model list: availible at
    https://huggingface.co/models?other=vit&sort=downloads
    """

    @dataclass
    class Config:
        image_size: list = field(default_factory=lambda: [224, 224])
        hidden_dropout_prob: float = 0
        hidden_size: int = 768
        patch_size: int = 16
        num_channels: int = 3
        random_init: bool = True
        pretrained_model_name: str = "google/vit-base-patch16-224"

    def __init__(self, config: Config):
        super().__init__()
        self.config = config
        self.embedding = ViTEncoder(self.config).embeddings
        self.token_type_embeddings = nn.Embedding(1, self.config.hidden_size)

    def forward(self, image):
        if image.dim() == 5:
            # manual collation for SimCLR inputs (when VISSL collator is not used)
            # make num_view the 1st dimension to be consistent with VISSL SimCLR
            image = image.permute(1, 0, 2, 3, 4).flatten(start_dim=0, end_dim=1)

        img_embeddings = self.embedding(image)

        img_segment_ids = torch.zeros(
            img_embeddings.size()[:-1],
            dtype=img_embeddings.dtype,
            device=img_embeddings.device,
        ).long()
        img_type_embed = self.token_type_embeddings(img_segment_ids)
        img_embeddings = img_embeddings + img_type_embed
        return img_embeddings


class ViLTTextEmbedding(nn.Module):
    @dataclass
    class Config:
        hidden_dim: int = 768
        hidden_size: int = 768
        bert_model_name: str = "bert-base-uncased"

    def __init__(self, config: Config):

        super().__init__()
        self.config = config
        text_encoder = TransformerEncoder(self.config)
        self.text_embeddings = text_encoder.embeddings
        encoder_output_dim = self.config.hidden_dim
        self.text_projection = nn.Linear(
            text_encoder.config.hidden_size, encoder_output_dim
        )

    def forward(self, input_ids, segment_ids):
        text_embedding = self.text_embeddings(input_ids, token_type_ids=segment_ids)
        text_embedding = self.text_projection(text_embedding)
        return text_embedding


@registry.register_model("vilt")
class ViLT(BaseModel):
    @dataclass
    class Config(BaseModel.Config):
        name: str = "ViLT"
        text_embeddings: ViLTTextEmbedding.Config = ViLTTextEmbedding.Config()
        image_embeddings: ViLTImageEmbedding.Config = ViLTImageEmbedding.Config()
        image_encoder: Any = MISSING

    @classmethod
    def config_path(cls):
        return "configs/models/vilt/defaults.yaml"

    def build(self):
        self.text_embeddings = ViLTTextEmbedding(self.config.text_embeddings)
        self.image_embeddings = ViLTImageEmbedding(self.config.image_embeddings)
        self.encoder = build_encoder(self.config.image_encoder)

        head_configs = self.config.get("heads", {})
        self.tasks = self.config.get("tasks", head_configs.keys())
        if isinstance(self.tasks, str):
            self.tasks = self.tasks.split(",")

        self.losses = nn.ModuleDict()
        # heads: Union[ nn.ModuleList, nn.ModuleDict ]
        # loss_names: Union[ list, dict ]
        self.heads_dict = HeadsDict.build_heads(head_configs, self.tasks, self.losses)

    def init_losses(self):
        loss_configs = self.config.get("losses", {})
        for loss_name, loss_config in loss_configs.items():
            self.losses[loss_name] = MMFLoss(loss_config)

    def forward(self, sample_list: Dict[str, Tensor]) -> Dict[str, Tensor]:
        text_embedding = self.text_embeddings(
            sample_list["input_ids"], sample_list["segment_ids"]
        )
        image_embedding = self.image_embeddings(sample_list["image"])

        # Feed through encoder
        embeddings = torch.cat([image_embedding, text_embedding], dim=1)
        attention_mask = self.get_attention_mask(
            sample_list, text_embedding, image_embedding
        )
        sequence, _ = self.encoder(embeddings, attention_mask=attention_mask)
        if sequence.dim() != 3:
            sequence = sequence.unsqueeze(1)

        outputs = self.heads_dict(sample_list.dataset_name, sequence, sample_list)
        return outputs

    def get_optimizer_parameters(self, config):
        if hasattr(self.encoder, "get_optimizer_parameters"):
            params = self.encoder.get_optimizer_parameters(config)
        else:
            params = [{"params": self.encoder.parameters()}]
        params += get_bert_configured_parameters(self.text_embeddings)
        params += get_bert_configured_parameters(self.heads_dict)
        params += [{"params": self.image_embeddings.parameters()}]
        return params

    def get_attention_mask(self, sample_list, text_embedding, image_embedding):
        image_mask = getattr(sample_list, "image_mask", None)

        if image_mask is not None and sample_list.input_mask is not None:
            attention_mask = torch.cat((sample_list.input_mask, image_mask), dim=-1)
        elif image_mask is not None:
            text_mask = torch.ones(
                text_embedding.size()[:-1],
                dtype=text_embedding.dtype,
                device=text_embedding.device,
            )
            attention_mask = torch.cat((image_mask, text_mask), dim=-1)
        elif sample_list.input_mask is not None:
            image_mask = torch.ones(
                image_embedding.size()[:-1],
                dtype=image_embedding.dtype,
                device=image_embedding.device,
            )
            attention_mask = torch.cat((image_mask, sample_list.input_mask), dim=-1)
        else:
            attention_mask = None

        if attention_mask is not None:
            attention_mask = attention_mask.masked_fill(
                ~attention_mask.bool(), float("-inf")
            )
            attention_mask = attention_mask[:, None, None, :]

        return attention_mask
