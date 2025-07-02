import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import investpy
import datetime

st.set_page_config(page_title="Análise de Ponto Pivô", layout="centered")
st.title("📊 Análise de Ponto Pivô com Gráfico de Candles")

ticker_input = st.text_input("Digite o ticker do ativo (ex: SPY, AAPL, PETR4):", value="SPY")
selected_date = st.date_input("Selecione a data de análise", datetime.date.today() - datetime.timedelta(days=1))

if st.button("Analisar"):
    with st.spinner("🔍 Buscando dados..."):
        data = yf.download(ticker_input.upper(), period="5d", interval="1d")

    if data.empty or len(data) < 2:
        st.error("❌ Dados insuficientes para esse ativo.")
    else:
        data.index = pd.to_datetime(data.index)
        selected_data = data[data.index.date == selected_date]

        if selected_data.empty:
            st.error(f"❌ Não há dados de mercado para {selected_date.strftime('%d/%m/%Y')}. Verifique se é um dia útil.")
        else:
            last_day = selected_data.iloc[0]
            date_str = selected_date.strftime("%d-%b-%Y")

            open_ = float(last_day["Open"])
            high = float(last_day["High"])
            low = float(last_day["Low"])
            close = float(last_day["Close"])

            pivot = (high + low + close) / 3.0
            r1 = (2 * pivot) - low
            s1 = (2 * pivot) - high
            r2 = pivot + (r1 - s1)
            s2 = pivot - (r1 - s1)

            st.subheader(f"📅 Dados de {ticker_input.upper()} em {date_str}")

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

            # Gráfico de Candles
            df = data[data.index.weekday < 5].tail(10).copy().reset_index()
            fig, ax = plt.subplots(figsize=(10, 5))

            x = range(len(df))  # eixo categórico

            for i, (_, row) in enumerate(df.iterrows()):
                o = float(row["Open"])
                h = float(row["High"])
                l = float(row["Low"])
                c = float(row["Close"])
                color = "green" if c >= o else "red"

                ax.plot([x[i], x[i]], [l, h], color="black")
                ax.plot([x[i], x[i]], [o, c], color=color, linewidth=6)

            # Linhas dos pivôs
            pivots = [
                (pivot, "Pivô", "purple"),
                (r1, "R1", "green"), (r2, "R2", "darkgreen"),
                (s1, "S1", "red"), (s2, "S2", "darkred"),
            ]
            for level, label, color in pivots:
                ax.axhline(level, color=color, linestyle="--", linewidth=1)
                ax.text(x[-1], level, label, color=color, va="center", fontsize=9)

            # Eixo X categórico sem dias vazios
            ax.set_xticks(x)
            ax.set_xticklabels(df["Date"].dt.strftime("%d-%b"), rotation=45)

            ax.set_title(f"{ticker_input.upper()} – Candles & Pontos Pivô")
            ax.set_ylabel("Preço (USD)")
            ax.grid(True)
            plt.tight_layout()
            st.pyplot(fig)


            # Calendário Econômico
            try:
                today = datetime.date.today()
                from_date = today.strftime("%d/%m/%Y")
                to_date = (today + datetime.timedelta(days=1)).strftime("%d/%m/%Y")

                df_events = investpy.news.economic_calendar(
                    from_date=from_date,
                    to_date=to_date,
                    countries=['United States'],
                    importances=['high']
                )

                # Filtra para manter apenas os eventos do dia atual
                df_events['date'] = pd.to_datetime(df_events['date'], format='%d/%m/%Y').dt.date
                df_events_today = df_events[df_events['date'] == today]

                if not df_events_today.empty:
                    st.subheader("📈 Calendário Econômico (EUA - Hoje)")
                    st.dataframe(df_events_today[['date', 'time', 'event', 'importance', 'actual', 'forecast', 'previous']])
                else:
                    st.info("Nenhum evento relevante para os EUA hoje.")
            except Exception as e:
                st.warning(f"Erro ao buscar o calendário econômico: {e}")
