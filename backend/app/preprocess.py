
import re
import pandas as pd
from typing import Tuple
from sklearn.model_selection import train_test_split

def clean_text(t: str) -> str:
    if not isinstance(t, str):
        return ""
    t = t.lower()
    t = re.sub(r"http\S+", " URL ", t)
    t = re.sub(r"\b[\w\.-]+@[\w\.-]+\.\w+\b", " EMAIL ", t)
    t = re.sub(r"[^a-z0-9\s@_#:$%!?.,']", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

def load_datasets(enron_path, sa_path):
    import pandas as pd

    print("Loading datasets...")

    # --- Load Enron ---
    enron = pd.read_csv(enron_path)
    if "Message" in enron.columns and "Spam/Ham" in enron.columns:
        enron = enron.rename(columns={
            "Message": "text",
            "Spam/Ham": "label"
        })
        enron["label"] = enron["label"].map({"spam": 1, "ham": 0})

    # --- Load SpamAssassin ---
    sa = pd.read_csv(sa_path)
    if "target" in sa.columns:
        sa = sa.rename(columns={"target": "label"})
    if "Spam/Ham" in sa.columns and "Message" in sa.columns:
        sa = sa.rename(columns={
            "Message": "text",
            "Spam/Ham": "label"
        })
        sa["label"] = sa["label"].map({"spam": 1, "ham": 0})

    # --- Keep only required cols ---
    enron = enron[["text", "label"]]
    sa = sa[["text", "label"]]

    # --- Merge datasets ---
    df = pd.concat([enron, sa], ignore_index=True)

    # 🚨 Clean invalid rows
    df = df.dropna(subset=["text"])                     # remove NaN
    df["text"] = df["text"].astype(str)                 # force to string
    df = df[df["text"].str.strip() != ""]               # remove empty text

    print(f"Samples: {len(df)} | Spam rate: {df['label'].mean():.3f}")
    return df



def split_xy(df, test_size=0.1, val_size=0.1, random_state=42):
    X = df["text"].tolist()
    y = df["label"].astype(int).tolist()
    from sklearn.model_selection import train_test_split
    X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=test_size+val_size, random_state=random_state, stratify=y)
    rel_val = val_size / (test_size + val_size)
    X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=1-rel_val, random_state=random_state, stratify=y_temp)
    return (X_train, y_train), (X_val, y_val), (X_test, y_test)
