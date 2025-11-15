import asyncio
import random
from io import BytesIO

import qrcode
import streamlit as st

from tropicalcode.settings import Settings

SETTINGS = Settings()

st.set_page_config(layout="centered")
st.title("Gerador de QR Code com Chave Dinâmica")
st.markdown("---")


async def main():
    code = str(random.randint(1000, 9999))

    base_url = SETTINGS.URL_SAIDA

    separator = "&" if "?" in base_url else "?"

    full_url = f"{base_url}{separator}chave={code}"

    try:
        img = qrcode.make(full_url)
        buffer = BytesIO()
        img.save(buffer, format="PNG")

        st.subheader("QR Code Gerado")

        st.image(
            buffer.getvalue(),
            caption=f"Escaneie para acessar com a chave: {code}",
            use_container_width=True,
        )

        st.markdown("---")
        st.subheader("Código de Acesso de 4 Dígitos")
        st.metric(label="Chave Única", value=code)
        st.write(full_url)
    except Exception as e:
        st.error(f"Ocorreu um erro ao gerar o QR Code: {e}")


if __name__ == "__main__":
    asyncio.run(main())
