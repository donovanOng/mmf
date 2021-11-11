# CE7454

## Image and Text Augmentation

### Image Augmentation

TBA...

### Text Augmentation

#### 1. [nlpaug](https://github.com/makcedward/nlpaug) (TA)

* Randomly swap, delete and substitute words at p=0.3
* Randomly select 1700 augmented train instances and add to training set

```bash
# Train model with 1700 additional randomly augmented memes
./scripts/train_ta.sh
```

#### 2. [paraphrase](https://github.com/PrithivirajDamodaran/Parrot_Paraphraser) (TP)

* Paraphrase with `prithivida/parrot_paraphraser_on_T5`
* Randomly select 1700 augmented train instances and add to training set

```bash
# Train model with 1700 additional paraphrased memes
./scripts/train_tp.sh
```

#### 3. TA + TP

```bash
# Train model with 34000 additional augmented memes
./scripts/train_tatp.sh
```

