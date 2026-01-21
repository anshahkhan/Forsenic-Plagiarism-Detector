# visuals_page.py
import streamlit as st
import plotly.graph_objects as go
import pandas as pd

def show_full_visuals(df: pd.DataFrame, module3_output: dict):
    container = st.container()

    # Close button
    if st.button("✕ Close Visuals"):
        container.empty()
        st.session_state.show_visuals_overlay = False
        return

    st.markdown("<h2 style='color:#111; font-weight:700; margin-bottom:12px;'>📊 Plagiarism Match Analysis</h2>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([2, 1.3, 1.3])
    chart_height = 400

    # --- BAR CHART CARD ---
    with col1:
        st.markdown("""
        <div style="
            padding:16px; border-radius:12px; background:#fff;
            box-shadow:0 4px 12px rgba(0,0,0,0.08); margin-bottom:16px;
        ">
        """, unsafe_allow_html=True)

        match_ids = [f"Match {i+1}" for i in range(len(df))]
        hover_texts = df["Sentence"]

        fig_bar = go.Figure(go.Bar(
            x=match_ids,
            y=df["Max Score (%)"],
            text=df["Max Score (%)"].astype(str) + "%",
            textposition="outside",
            marker=dict(color=df["Color"]),
            hovertext=hover_texts,
            hoverinfo="text+y"
        ))
        fig_bar.update_layout(
            height=chart_height,
            margin=dict(t=40, b=60),
            paper_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(title="Max Score (%)", range=[0, 100]),
            xaxis=dict(title="Match ID")
        )
        st.plotly_chart(fig_bar, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # --- PIE CHART CARD ---
    with col2:
        st.markdown("""
        <div style="
            padding:16px; border-radius:12px; background:#fff;
            box-shadow:0 4px 12px rgba(0,0,0,0.08); margin-bottom:16px;
        ">
        """, unsafe_allow_html=True)

        strengths = {"strong":0, "medium":0, "weak":0}
        match_labels = {"strong": [], "medium": [], "weak": []}

        for idx, item in enumerate(module3_output["results"]):
            scores = [s.get("score",0)*100 for s in item.get("sources",[])]
            if not scores:
                continue
            mx = max(scores)
            match_label = f"Match {idx+1}"
            if mx >= 80:
                strengths["strong"] += 1
                match_labels["strong"].append(match_label)
            elif mx >= 50:
                strengths["medium"] += 1
                match_labels["medium"].append(match_label)
            else:
                strengths["weak"] += 1
                match_labels["weak"].append(match_label)

        fig_pie = go.Figure(go.Pie(
            labels=[f"Strong (Red): {', '.join(match_labels['strong'])}" if match_labels['strong'] else "Strong (Red)",
                    f"Medium (Orange): {', '.join(match_labels['medium'])}" if match_labels['medium'] else "Medium (Orange)",
                    f"Weak (Yellow): {', '.join(match_labels['weak'])}" if match_labels['weak'] else "Weak (Yellow)"],
            values=[strengths["strong"], strengths["medium"], strengths["weak"]],
            hole=0,
            marker=dict(colors=["#FF3B30","#FF9500","#FFCC00"]),
            textinfo="label+percent"
        ))
        fig_pie.update_layout(height=chart_height, paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_pie, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # --- DONUT CHART CARD ---
    with col3:
        st.markdown("""
        <div style="
            padding:16px; border-radius:12px; background:#fff;
            box-shadow:0 4px 12px rgba(0,0,0,0.08); margin-bottom:16px;
        ">
        """, unsafe_allow_html=True)

        sources_count = [len(item.get("sources",[])) for item in module3_output["results"]]
        match_ids_labels = [f"Match {i+1}" for i in range(len(module3_output["results"]))]

        fig_donut = go.Figure(go.Pie(
            labels=match_ids_labels,
            values=sources_count,
            hole=0.5,
            marker=dict(colors=df["Color"]),
            textinfo="label+value"
        ))
        fig_donut.update_layout(height=chart_height, paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_donut, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
