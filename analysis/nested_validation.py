from dataclasses import dataclass


@dataclass(frozen=True)
class TemporalFold:
    train: range
    validation: range
    test: range


def expanding_temporal_folds(
    sample_count,
    minimum_train,
    validation_size,
    test_size,
    step=None,
):
    if min(sample_count, minimum_train, validation_size, test_size) < 1:
        raise ValueError("Temporal fold boyutları pozitif olmalıdır.")
    step = step or test_size
    folds = []
    train_end = minimum_train
    while train_end + validation_size + test_size <= sample_count:
        validation_end = train_end + validation_size
        test_end = validation_end + test_size
        folds.append(
            TemporalFold(
                train=range(0, train_end),
                validation=range(train_end, validation_end),
                test=range(validation_end, test_end),
            )
        )
        train_end += step
    return folds


def assert_no_temporal_leakage(fold):
    if not fold.train or not fold.validation or not fold.test:
        raise ValueError("Fold bölümleri boş olamaz.")
    if max(fold.train) >= min(fold.validation) or max(fold.validation) >= min(fold.test):
        raise AssertionError("Temporal fold içinde look-ahead sızıntısı var.")
