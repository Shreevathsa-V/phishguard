
import os, json
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.preprocessing.text import tokenizer_from_json

MAX_LEN = int(os.getenv("MAX_LEN", "200"))

def load_model(path: str):
    return tf.keras.models.load_model(path)

def load_tokenizer(path: str):
    with open(path, "r") as f:
        data = f.read()
    return tokenizer_from_json(data)

def predict_texts(model, tokenizer, texts):
    seqs = tokenizer.texts_to_sequences(texts)
    padded = pad_sequences(seqs, maxlen=MAX_LEN, padding="post", truncating="post")
    preds = model.predict(padded, verbose=0).squeeze()
    if preds.ndim == 0:
        preds = np.array([float(preds)])
    return preds
