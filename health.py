import platform
import streamlit as st

st.title("✅ ทดสอบระบบ")
st.write(f"Streamlit {st.__version__} · Python {platform.python_version()}")
st.write("ถ้าเห็นหน้านี้ แสดงว่า Streamlit Cloud และเครือข่ายของคุณปกติ")
