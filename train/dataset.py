import os
from typing import Optional, Tuple

import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset, random_split
from sklearn.preprocessing import StandardScaler


class MalwareDataset(Dataset):
    """Dataset for malware features stored in CSV or Parquet files.

    The feature file is expected to contain a label column (default ``label``)
    along with numeric feature columns. Optionally a :class:`~sklearn.preprocessing.StandardScaler`
    can be applied to normalise the features.
    """

    def __init__(
        self,
        file_path: str,
        label_col: str = "label",
        normalize: bool = False,
        scaler: Optional[StandardScaler] = None,
    ) -> None:
        super().__init__()
        self.file_path = file_path
        self.label_col = label_col

        # Read the feature file depending on the extension
        if file_path.lower().endswith(".csv"):
            df = pd.read_csv(file_path)
        elif file_path.lower().endswith(".parquet"):
            df = pd.read_parquet(file_path)
        else:
            raise ValueError(
                f"Unsupported file type '{os.path.splitext(file_path)[1]}'. "
                "Only CSV and Parquet are supported."
            )

        if label_col not in df.columns:
            raise ValueError(f"Label column '{label_col}' not found in {file_path}")

        # Extract labels and features
        self.labels = torch.tensor(df[label_col].to_numpy(), dtype=torch.long)
        features = df.drop(columns=[label_col]).to_numpy(dtype=np.float32)

        # Optional normalization
        self.scaler = scaler
        if normalize:
            if self.scaler is None:
                self.scaler = StandardScaler()
                self.scaler.fit(features)
            features = self.scaler.transform(features)

        self.features = torch.from_numpy(features.astype(np.float32))

    def __len__(self) -> int:
        return len(self.labels)

    def __getitem__(self, idx: int):
        return self.features[idx], self.labels[idx]


def train_val_split(
    dataset: Dataset,
    val_ratio: float = 0.2,
    seed: Optional[int] = 42,
) -> Tuple[Dataset, Dataset]:
    """Split a dataset into training and validation subsets.

    Parameters
    ----------
    dataset:
        The dataset to split.
    val_ratio:
        Fraction of samples to use for validation.
    seed:
        Optional random seed for reproducibility.
    """
    val_size = int(len(dataset) * val_ratio)
    train_size = len(dataset) - val_size
    generator = torch.Generator()
    if seed is not None:
        generator.manual_seed(seed)
    return random_split(dataset, [train_size, val_size], generator=generator)


def load_train_val_datasets(
    file_path: str,
    label_col: str = "label",
    val_ratio: float = 0.2,
    normalize: bool = False,
    seed: Optional[int] = 42,
) -> Tuple[Dataset, Dataset]:
    """Convenience helper to load a feature file and obtain train/val splits."""
    dataset = MalwareDataset(file_path, label_col=label_col, normalize=normalize)
    return train_val_split(dataset, val_ratio=val_ratio, seed=seed)
