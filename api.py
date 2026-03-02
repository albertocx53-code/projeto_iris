from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import tempfile
import os

from utils import load_iris_csv
from estatistica import mean, median, mode, variance, std_dev
from frequencia import (
    freq_nao_agrupada,
    classes_por_sturges,
    freq_agrupada,
    grouped_mean,
    grouped_median,
    grouped_variance,
    grouped_std_dev
)

app = FastAPI(title="Projeto Iris - TDE")

# ✅ Permite acesso do site online
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

VALID_ATTRS = {
    "sepal_length",
    "sepal_width",
    "petal_length",
    "petal_width"
}

VALID_SPECIES = {
    "setosa",
    "versicolor",
    "virginica",
    "all"
}


@app.get("/")
def home():
    return {"ok": True, "msg": "API Iris Online 🚀"}


@app.post("/analyze")
async def analyze(
    csv_file: Optional[UploadFile] = File(None),
    attribute: str = Form(...),
    species: str = Form("all")
):

    attribute = attribute.strip().lower()
    species = species.strip().lower()

    if attribute not in VALID_ATTRS:
        return {"ok": False, "error": "Atributo inválido"}

    if species not in VALID_SPECIES:
        return {"ok": False, "error": "Espécie inválida"}

    # ✅ usa CSV embutido se não enviar arquivo OU se vier vazio
if (csv_file is None) or (not getattr(csv_file, "filename", "").strip()):
    data = load_iris_csv("iris.csv")
else:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        content = await csv_file.read()
        tmp.write(content)
        tmp_path = tmp.name

    data = load_iris_csv(tmp_path)
    try:
        os.remove(tmp_path)
    except:
        pass

    else:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
            content = await csv_file.read()
            tmp.write(content)
            tmp_path = tmp.name

        data = load_iris_csv(tmp_path)

        try:
            os.remove(tmp_path)
        except:
            pass

    if not data:
        return {"ok": False, "error": "Dataset vazio"}

    species_filter = None if species == "all" else species

    valores = [
        r[attribute]
        for r in data
        if species_filter is None
        or r["species_norm"] == species_filter
    ]

    if len(valores) == 0:
        return {"ok": False, "error": "Nenhum dado encontrado"}

    # =====================
    # Estatística
    # =====================
    raw = {
        "n": len(valores),
        "mean": mean(valores),
        "median": median(valores),
        "mode": mode(valores),
        "variance": variance(valores),
        "std_dev": std_dev(valores),
    }

    # =====================
    # Frequência agrupada
    # =====================
    k, h, lower, upper = classes_por_sturges(valores)
    tabela = freq_agrupada(valores, k, h, lower, upper)

    fac = 0
    grouped = []

    for r in tabela:
        fac += r["fi"]
        grouped.append({
            "label": f"{r['lower']:.2f} |-- {r['upper']:.2f}",
            "fi": r["fi"],
            "fac": fac,
            "fr": r["fi"] / len(valores)
        })

    grouped_stats = {
        "k": k,
        "h": h,
        "mean": grouped_mean(tabela),
        "median": grouped_median(tabela),
        "variance": grouped_variance(tabela),
        "std_dev": grouped_std_dev(tabela)
    }

    return {
        "ok": True,
        "attribute": attribute,
        "species": species,
        "raw": raw,
        "freq_grouped": grouped,
        "grouped_stats": grouped_stats
    }
