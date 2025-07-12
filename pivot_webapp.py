import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import investpy
import datetime

# Configurações da página
st.set_page_config(page_title="Análise de Ponto Pivô", layout="centered")
st.title("📊 Análise de Ponto Pivô com Gráfico de Candles")

# Inicializa o estado
if "ticker_input" not in st.session_state:
    st.session_state.ticker_input = "SPY"
if "selected_date" not in st.session_state:
    st.session_state.selected_date = datetime.date.today() - datetime.timedelta(days=1)
if "analisar" not in st.session_state:
    st.session_state.analisar = False

# Entradas do usuário
st.session_state.ticker_input = st.text_input(
    "Digite o ticker do ativo (ex: SPY, AAPL, PETR4):",
    value=st.session_state.ticker_input
)
st.session_state.selected_date = st.date_input(
    "Selecione a data de análise",
    value=st.session_state.selected_date
)

if st.button("Analisar"):
    st.session_state.analisar = True

# Início da análise
if st.session_state.analisar:
    with st.spinner("🔍 Buscando dados..."):
        data = yf.download(st.session_state.ticker_input.upper(), period="7d", interval="1d")

    if data.empty or len(data) < 2:
        st.error("❌ Dados insuficientes para esse ativo.")
    else:
        data.index = pd.to_datetime(data.index)
        selected_data = data[data.index.date == st.session_state.selected_date]

        if selected_data.empty:
            st.error(f"❌ Não há dados de mercado para {st.session_state.selected_date.strftime('%d/%m/%Y')}. Verifique se é um dia útil.")
        else:
            last_day = selected_data.iloc[0]
            date_str = st.session_state.selected_date.strftime("%d-%b-%Y")

            open_ = float(last_day["Open"])
            high = float(last_day["High"])
            low = float(last_day["Low"])
            close = float(last_day["Close"])

            pivot = (high + low + close) / 3.0
            r1 = (2 * pivot) - low
            s1 = (2 * pivot) - high
            r2 = pivot + (r1 - s1)
            s2 = pivot - (r1 - s1)

            st.subheader(f"📅 Dados de {st.session_state.ticker_input.upper()} em {date_str}")

            # Tabela OHLC
            ohlc_df = pd.DataFrame({
                "Indicador": ["Open", "High", "Low", "Close"],
                "Valor": [open_, high, low, close]
            })
            st.markdown("### 📌 Valores OHLC")
            st.dataframe(
                ohlc_df.style.format({"Valor": "{:.2f}"}),
                use_container_width=True
            )

            # Tabela de Pivôs
            pivot_df = pd.DataFrame({
                "Indicador": ["Pivô", "R1", "R2", "S1", "S2"],
                "Valor": [pivot, r1, r2, s1, s2]
            })
            st.markdown("### 🎯 Níveis de Ponto Pivô")
            st.dataframe(
                pivot_df.style.format({"Valor": "{:.2f}"}).highlight_max(color='lightgreen').highlight_min(color='lightcoral'),
                use_container_width=True
            )

            # Gráfico de Candles (sem espaços de fim de semana)
            df = data[data.index.weekday < 5].tail(10).copy()
            df["Date"] = pd.to_datetime(df.index)

            fig, ax = plt.subplots(figsize=(10, 5))
            for idx, row in df.iterrows():
                o = float(row["Open"])
                h = float(row["High"])
                l = float(row["Low"])
                c = float(row["Close"])
                color = "green" if c >= o else "red"
                date = row["Date"]

                ax.plot([date, date], [l, h], color="black")
                ax.plot([date, date], [o, c], color=color, linewidth=6)

            # Linhas dos Pivôs
            pivots = [
                (pivot, "Pivô", "purple"),
                (r1, "R1", "green"), (r2, "R2", "darkgreen"),
                (s1, "S1", "red"), (s2, "S2", "darkred"),
            ]
            for level, label, color in pivots:
                ax.axhline(level, color=color, linestyle="--", linewidth=1)
                ax.text(df["Date"].iloc[-1], level, label, color=color, va="center", fontsize=9)

            ax.set_title(f"{st.session_state.ticker_input.upper()} – Candles & Pontos Pivô")
            ax.set_ylabel("Preço (USD)")
            ax.set_xlabel("Data")
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%d-%b"))
            ax.set_xticks(df["Date"])  # Garante que só datas úteis são exibidas
            ax.grid(True)
            plt.tight_layout()
            st.pyplot(fig)

# Calendário Econômico
st.subheader("📆 Calendário Econômico (EUA)")

col1, col2 = st.columns(2)
with col1:
    econ_date = st.date_input("Selecione a data do calendário econômico", datetime.date.today(), key="econ_date")
with col2:
    importance = st.selectbox("Relevância", ["high", "medium", "low"], index=0, key="importance")

try:
    from_date = econ_date.strftime("%d/%m/%Y")
    to_date = (econ_date + datetime.timedelta(days=1)).strftime("%d/%m/%Y")

    df_events = investpy.news.economic_calendar(
        from_date=from_date,
        to_date=to_date,
        countries=['United States'],
        importances=[importance]
    )

    if not df_events.empty:
        st.dataframe(df_events[['date', 'time', 'event', 'importance', 'actual', 'forecast', 'previous']])
    else:
        st.info("Nenhum evento relevante para os EUA na data selecionada.")
except Exception as e:
    st.warning(f"Erro ao buscar o calendário econômico: {e}")
