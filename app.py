import streamlit as st
import networkx as nx

st.title("🧪 NetworkX 测试应用")

st.success(f"✅ 成功导入 NetworkX! 版本: {nx.__version__}")

if st.button("生成一个简单的图"):
    G = nx.Graph()
    G.add_edge("A", "B")
    G.add_edge("B", "C")
    st.write(f"图创建成功！节点数: {G.number_of_nodes()}, 边数: {G.number_of_edges()}")
    st.success("🎉 NetworkX 功能完全正常！")
