#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
App Streamlit - Gestione Finanze Personali
Frontend completo con rate automatiche e stati
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from budget import *

# ============================================
# CONFIGURAZIONE PAGINA
# ============================================

st.set_page_config(
    page_title="💰 Gestione Finanze",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Custom
st.markdown("""
<style>
    .stAlert {
        border-radius: 10px;
    }
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# INIZIALIZZAZIONE SESSION STATE
# ============================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None
if "supabase" not in st.session_state:
    try:
        st.session_state.supabase = get_supabase_client()
    except Exception as e:
        st.error(f"❌ Errore connessione Supabase: {e}")
        st.stop()
if "vista_corrente" not in st.session_state:
    st.session_state.vista_corrente = "dashboard"
if "anno_selezionato" not in st.session_state:
    st.session_state.anno_selezionato = datetime.now().year
if "mese_selezionato" not in st.session_state:
    st.session_state.mese_selezionato = datetime.now().month

# ============================================
# AUTENTICAZIONE
# ============================================

def mostra_login():
    """Pagina di login/registrazione"""
    st.title("💰 Gestione Finanze Personali")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab_login, tab_register = st.tabs(["🔐 Login", "📝 Registrazione"])
        
        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Email", key="login_email")
                password = st.text_input("Password", type="password", key="login_password")
                submitted = st.form_submit_button("Accedi", use_container_width=True)
                
                if submitted:
                    if not email or not password:
                        st.error("Inserisci email e password")
                    else:
                        auth = AuthManager(st.session_state.supabase)
                        result = auth.login(email, password)
                        
                        if result["success"]:
                            st.session_state.logged_in = True
                            st.session_state.user = result["user"]
                            st.success("✅ Login effettuato!")
                            st.rerun()
                        else:
                            st.error(f"❌ Errore: {result['error']}")
        
        with tab_register:
            with st.form("register_form"):
                email_reg = st.text_input("Email", key="reg_email")
                password_reg = st.text_input("Password (min 6 caratteri)", type="password", key="reg_password")
                password_conf = st.text_input("Conferma Password", type="password", key="reg_password_conf")
                submitted_reg = st.form_submit_button("Registrati", use_container_width=True)
                
                if submitted_reg:
                    if not email_reg or not password_reg:
                        st.error("Compila tutti i campi")
                    elif len(password_reg) < 6:
                        st.error("Password deve essere almeno 6 caratteri")
                    elif password_reg != password_conf:
                        st.error("Le password non corrispondono")
                    else:
                        auth = AuthManager(st.session_state.supabase)
                        result = auth.register(email_reg, password_reg)
                        
                        if result["success"]:
                            st.success("✅ Registrazione completata! Controlla l'email per conferma.")
                            
                            user_id = result["user"].id
                            CategorieManager(st.session_state.supabase, user_id).inizializza_categorie_default()
                            ContiManager(st.session_state.supabase, user_id).inizializza_conti_default()
                            
                            st.info("Ora puoi effettuare il login")
                        else:
                            st.error(f"❌ Errore: {result['error']}")


# ============================================
# SIDEBAR
# ============================================

def mostra_sidebar():
    """Sidebar con navigazione e saldi"""
    with st.sidebar:
        st.title("💰 Menu")
        
        if st.session_state.user:
            st.info(f"👤 {st.session_state.user.email}")
        
        user_id = st.session_state.user.id
        mov_mgr = MovimentiManager(st.session_state.supabase, user_id)
        mov_mgr.aggiorna_stati_automatico()

        
        # Mostra badge se ci sono stati aggiornamenti recenti
        aggiornamenti = st.session_state.get("ultimi_aggiornamenti")
        if aggiornamenti and aggiornamenti.get("aggiornati", 0) > 0:
            st.success(f"✅ {aggiornamenti['aggiornati']} movimento/i contabilizzato/i oggi!")
            
            # Reset dopo visualizzazione
            if st.button("👍 OK", key="reset_notifica"):
                st.session_state.ultimi_aggiornamenti = None
                st.rerun()
        
        st.divider()
        
        vista = st.radio(
            "Navigazione",
            ["🏠 Dashboard", "📊 Movimenti", "💳 Conti", "📈 Statistiche", "⚙️ Impostazioni"],
            label_visibility="collapsed"
        )
        
        vista_map = {
            "🏠 Dashboard": "dashboard",
            "📊 Movimenti": "movimenti",
            "💳 Conti": "conti",
            "📈 Statistiche": "statistiche",
            "⚙️ Impostazioni": "impostazioni"
        }
        st.session_state.vista_corrente = vista_map[vista]
        
        st.divider()
        
        st.subheader("💵 Saldi Conti")
        
        try:
            conti_mgr = ContiManager(st.session_state.supabase, st.session_state.user.id)
            saldi = conti_mgr.get_saldi_conti()
            
            for nome, saldo in saldi.items():
                if nome != "TOTALE":
                    colore = "normal" if saldo >= 0 else "inverse"
                    st.metric(nome.capitalize(), f"€ {saldo:,.2f}", delta_color=colore)
            
            st.divider()
            st.metric("💰 Totale", f"€ {saldi.get('TOTALE', 0):,.2f}", delta_color="off")
            
        except Exception as e:
            st.error(f"Errore caricamento saldi: {e}")
        
        st.divider()
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.rerun()


# ============================================
# VISTA: DASHBOARD
# ============================================

def mostra_dashboard():
    """Dashboard principale"""
    st.title("🏠 Dashboard")
    
    user_id = st.session_state.user.id
    stats_mgr = StatisticheManager(st.session_state.supabase, user_id)
    conti_mgr = ContiManager(st.session_state.supabase, user_id)
    
    col_anno1, col_anno2, col_anno3 = st.columns([1, 2, 1])
    with col_anno2:
        anno_corrente = st.selectbox(
            "Anno",
            range(datetime.now().year - 5, datetime.now().year + 2),
            index=5,
            key="dash_anno"
        )
    
    riepilogo = stats_mgr.riepilogo_annuale(anno_corrente)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "💸 Entrate Totali",
            f"€ {riepilogo['totale_entrate']:,.2f}",
            delta=f"+{riepilogo['totale_entrate']:,.0f}"
        )
    
    with col2:
        st.metric(
            "💳 Uscite Totali",
            f"€ {riepilogo['totale_uscite']:,.2f}",
            delta=f"-{riepilogo['totale_uscite']:,.0f}",
            delta_color="inverse"
        )
    
    with col3:
        bilancio = riepilogo['bilancio_annuale']
        st.metric(
            "📊 Bilancio Anno",
            f"€ {bilancio:,.2f}",
            delta=f"{'+' if bilancio >= 0 else ''}{bilancio:,.0f}",
            delta_color="normal" if bilancio >= 0 else "inverse"
        )
    
    with col4:
        saldi = conti_mgr.get_saldi_conti()
        st.metric(
            "💰 Patrimonio",
            f"€ {saldi.get('TOTALE', 0):,.2f}"
        )
    
    st.divider()
    
    col_graf1, col_graf2 = st.columns(2)
    
    with col_graf1:
        st.subheader("📈 Trend Mensile")
        
        mesi_df = pd.DataFrame(riepilogo['mesi'])
        mesi_df['Bilancio'] = mesi_df['entrate_effettive'] - mesi_df['uscite_effettive']
        
        fig_trend = go.Figure()
        
        fig_trend.add_trace(go.Bar(
            x=mesi_df['nome_mese'],
            y=mesi_df['entrate_effettive'],
            name='Entrate',
            marker_color='#10b981'
        ))
        
        fig_trend.add_trace(go.Bar(
            x=mesi_df['nome_mese'],
            y=mesi_df['uscite_effettive'],
            name='Uscite',
            marker_color='#ef4444'
        ))
        
        fig_trend.add_trace(go.Scatter(
            x=mesi_df['nome_mese'],
            y=mesi_df['Bilancio'],
            name='Bilancio',
            mode='lines+markers',
            line=dict(color='#3b82f6', width=3),
            yaxis='y2'
        ))
        
        fig_trend.update_layout(
            barmode='group',
            yaxis=dict(title='Euro (€)'),
            yaxis2=dict(title='Bilancio (€)', overlaying='y', side='right'),
            hovermode='x unified',
            height=400
        )
        
        st.plotly_chart(fig_trend, use_container_width=True)
    
    with col_graf2:
        st.subheader("🎯 Spese per Categoria")
        
        mese_corrente = datetime.now().month
        categorie_stats = stats_mgr.statistiche_per_categoria(anno_corrente, mese_corrente)
        
        uscite_cat = [c for c in categorie_stats if c['tipo'] == 'uscita'][:8]
        
        if uscite_cat:
            cat_df = pd.DataFrame(uscite_cat)
            
            fig_cat = px.pie(
                cat_df,
                values='importo_totale',
                names='categoria',
                color='categoria',
                hole=0.4,
                height=400
            )
            
            fig_cat.update_traces(textposition='inside', textinfo='percent+label')
            
            st.plotly_chart(fig_cat, use_container_width=True)
        else:
            st.info("Nessun dato disponibile per questo mese")
    
    st.divider()
    
    st.subheader("📅 Riepilogo per Mese")
    
    mesi_display = []
    for m_data in riepilogo['mesi']:
        mesi_display.append({
            "Mese": m_data['nome_mese'],
            "Entrate": f"€ {m_data['entrate_effettive']:,.2f}",
            "Uscite": f"€ {m_data['uscite_effettive']:,.2f}",
            "Bilancio": f"€ {m_data['bilancio_effettivo']:,.2f}",
            "Movimenti": m_data['num_movimenti'],
            "_mese_num": m_data['mese']
        })
    
    df_mesi = pd.DataFrame(mesi_display)
    
    event = st.dataframe(
        df_mesi[["Mese", "Entrate", "Uscite", "Bilancio", "Movimenti"]],
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row"
    )
    
    if event.selection.rows:
        idx = event.selection.rows[0]
        mese_sel = df_mesi.iloc[idx]["_mese_num"]
        st.session_state.anno_selezionato = anno_corrente
        st.session_state.mese_selezionato = mese_sel
        st.session_state.vista_corrente = "movimenti"
        st.rerun()


# ============================================
# VISTA: MOVIMENTI
# ============================================

def mostra_movimenti():
    """Gestione movimenti con stati"""
    st.title("Gestione Movimenti")
    
    user_id = st.session_state.user.id
    mov_mgr = MovimentiManager(st.session_state.supabase, user_id)
    stats_mgr = StatisticheManager(st.session_state.supabase, user_id)
    
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col1:
        if st.button("⬅️ Mese Prec"):
            data_corrente = datetime(st.session_state.anno_selezionato, st.session_state.mese_selezionato, 1)
            data_prec = data_corrente - relativedelta(months=1)
            st.session_state.anno_selezionato = data_prec.year
            st.session_state.mese_selezionato = data_prec.month
            st.rerun()
    
    with col2:
        st.markdown(f"### 📅 {datetime(st.session_state.anno_selezionato, st.session_state.mese_selezionato, 1).strftime('%B %Y')}")
    
    with col3:
        if st.button("Mese Succ ➡️"):
            data_corrente = datetime(st.session_state.anno_selezionato, st.session_state.mese_selezionato, 1)
            data_succ = data_corrente + relativedelta(months=1)
            st.session_state.anno_selezionato = data_succ.year
            st.session_state.mese_selezionato = data_succ.month
            st.rerun()
    
    # Riepilogo mensile CON PREVISTI
    riepilogo = stats_mgr.riepilogo_mensile(st.session_state.anno_selezionato, st.session_state.mese_selezionato)
    
    col_m1, col_m2, col_m3, col_m4, col_m5, col_m6 = st.columns(6)
    
    with col_m1:
        st.metric("💚 Entrate", f"€ {riepilogo['entrate_effettive']:,.2f}")
    
    with col_m2:
        st.metric("💔 Uscite", f"€ {riepilogo['uscite_effettive']:,.2f}")
    
    with col_m3:
        bilancio = riepilogo['bilancio_effettivo']
        st.metric(
            "📊 Bilancio",
            f"€ {bilancio:,.2f}",
            delta_color="normal" if bilancio >= 0 else "inverse"
        )
    
    with col_m4:
        st.metric("🔮 Entrate Previste", f"€ {riepilogo['entrate_previste']:,.2f}")
    
    with col_m5:
        st.metric("🔮 Uscite Previste", f"€ {riepilogo['uscite_previste']:,.2f}")
    
    with col_m6:
        st.metric("📝 Movimenti", riepilogo['num_movimenti'])
    
    st.divider()
    
    # Form aggiunta movimento
    with st.expander("➕ Aggiungi Nuovo Movimento", expanded=False):
        mostra_form_movimento()
    
    st.divider()
    
    # Recupera movimenti del mese
    data_inizio = f"{st.session_state.anno_selezionato}-{st.session_state.mese_selezionato:02d}-01"
    ultimo_giorno = (datetime(st.session_state.anno_selezionato, st.session_state.mese_selezionato, 1) + relativedelta(months=1) - timedelta(days=1)).day
    data_fine = f"{st.session_state.anno_selezionato}-{st.session_state.mese_selezionato:02d}-{ultimo_giorno:02d}"
    
    movimenti = mov_mgr.get_movimenti(data_inizio=data_inizio, data_fine=data_fine, includi_pianificati=True)
    
    if not movimenti:
        st.info("📭 Nessun movimento registrato per questo mese")
        return
    
    # Prepara dataframe CON STATO
    mov_display = []
    for m in movimenti:
        from datetime import datetime as dt
        data_obj = dt.strptime(m['data'], "%Y-%m-%d").date() if isinstance(m['data'], str) else m['data']
        
        # Badge stato
        stato_badge = "✅ Contabilizzato" if m['stato'] == 'contabilizzata' else "🔮 Pianificato"
        
        mov_display.append({
            "ID": m['id'],
            "Data": data_obj,
            "Descrizione": m['descrizione'],
            "Categoria": m['categorie']['nome'] if m['categorie'] else "-",
            "Conto": m['conti']['nome'] if m['conti'] else "-",
            "Tipo": "💚 Entrata" if m['tipo'] == 'entrata' else "💔 Uscita",
            "Importo": f"€ {m['importo']:,.2f}",
            "Stato": stato_badge,
            "_id_raw": m['id'],
            "_stato_raw": m['stato']
        })
    
    df_mov = pd.DataFrame(mov_display)
    
    # Tabella movimenti
    st.subheader("📋 Elenco Movimenti")
    
    st.dataframe(
        df_mov[["Data", "Descrizione", "Categoria", "Conto", "Tipo", "Importo", "Stato"]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
            "Stato": st.column_config.TextColumn("Stato")
        }
    )
    
    # Elimina movimento
    st.divider()
    st.subheader("🗑️ Elimina Movimento")
    
    col_del1, col_del2 = st.columns([3, 1])
    
    with col_del1:
        mov_ids = [f"{m['ID']} - {m['Descrizione'][:50]}" for m in mov_display]
        movimento_sel = st.selectbox("Seleziona movimento da eliminare", mov_ids)
    
    with col_del2:
        st.write("")
        st.write("")
        if st.button("🗑️ Elimina", type="secondary"):
            if movimento_sel:
                movimento_id = int(movimento_sel.split(" - ")[0])
                
                # Conferma
                if st.session_state.get(f"conferma_elimina_{movimento_id}", False):
                    result = mov_mgr.elimina_movimento(movimento_id)
                    
                    if result["success"]:
                        st.success("✅ Movimento eliminato!")
                        st.session_state[f"conferma_elimina_{movimento_id}"] = False
                        st.rerun()
                    else:
                        st.error(f"❌ {result['error']}")
                else:
                    st.session_state[f"conferma_elimina_{movimento_id}"] = True
                    st.warning("⚠️ Clicca di nuovo per confermare l'eliminazione")
                    st.rerun()


def mostra_form_movimento():
    """Form interattivo per aggiungere movimenti, con gestione immediata dei movimenti periodici."""
    user_id = st.session_state.user.id
    cat_mgr = CategorieManager(st.session_state.supabase, user_id)
    conti_mgr = ContiManager(st.session_state.supabase, user_id)
    mov_mgr = MovimentiManager(st.session_state.supabase, user_id)

    st.subheader("➕ Aggiungi Movimento")

    # Checkbox fuori dal form, così aggiorna subito l'interfaccia
    periodico = st.checkbox("Movimento Periodico (Rate Mensili)")

    # Inizio form principale
    with st.form("form_movimento"):
        col1, col2 = st.columns(2)

        with col1:
            tipo = st.selectbox("Tipo*", ["entrata", "uscita"])
            descrizione = st.text_input("Descrizione*")
            importo = st.number_input("Importo (€)*", min_value=0.01, step=0.01)

        with col2:
            categorie = cat_mgr.get_categorie(tipo=tipo)
            categorie_nomi = [c['nome'] for c in categorie]
            categoria = st.selectbox("Categoria*", categorie_nomi if categorie_nomi else ["Altro"])

            conti = conti_mgr.get_conti()
            conti_dict = {c['nome']: c['id'] for c in conti}
            conto_nome = st.selectbox("Conto*", list(conti_dict.keys()) if conti_dict else ["Principale"])

        # --- MOVIMENTO PERIODICO ---
        data_movimento = None
        data_inizio = None
        numero_rate = None
        data_fine_calc = None

        if periodico:
            st.markdown("### 📅 Impostazioni movimento periodico")
            st.info("Verrà creata una rata per ogni mese. Rate con data ≤ oggi saranno contabilizzate, future saranno pianificate.")

            col_p1, col_p2, col_p3 = st.columns(3)
            with col_p1:
                data_inizio = st.date_input("Data Inizio (giorno della rata)", value=datetime.now())
            with col_p2:
                numero_rate = st.number_input("Numero Rate", min_value=1, max_value=120, value=3, step=1)
            with col_p3:
                if data_inizio and numero_rate:
                    data_fine_calc = data_inizio + relativedelta(months=numero_rate - 1)
                    st.date_input("Data Fine (auto)", value=data_fine_calc, disabled=True)

        # --- MOVIMENTO UNA TANTUM ---
        else:
            data_movimento = st.date_input("Data Movimento", value=datetime.now())
            data_str = data_movimento.strftime("%Y-%m-%d")
            stato_previsto = calcola_stato_movimento(data_str)
            if stato_previsto == "pianificata":
                st.info("🔮 Questo movimento sarà pianificato (data futura)")
            else:
                st.success("✅ Questo movimento sarà contabilizzato immediatamente")

        note = st.text_area("Note (opzionale)")

        submitted = st.form_submit_button("💾 Aggiungi Movimento", use_container_width=True)

        if submitted:
            if not descrizione or importo <= 0:
                st.error("Compila tutti i campi obbligatori")
                return

            conto_id = conti_dict[conto_nome]

            if periodico:
                if not data_inizio or not numero_rate:
                    st.error("Inserisci data di inizio e numero di rate")
                    return

                result = mov_mgr.aggiungi_movimento(
                    data=None,
                    descrizione=descrizione,
                    importo=importo,
                    categoria_nome=categoria,
                    tipo=tipo,
                    conto_id=conto_id,
                    periodico=True,
                    numero_rate=numero_rate,
                    data_inizio=data_inizio.strftime("%Y-%m-%d"),
                    note=note
                )
            else:
                result = mov_mgr.aggiungi_movimento(
                    data=data_movimento.strftime("%Y-%m-%d"),
                    descrizione=descrizione,
                    importo=importo,
                    categoria_nome=categoria,
                    tipo=tipo,
                    conto_id=conto_id,
                    periodico=False,
                    note=note
                )

            if result["success"]:
                if periodico:
                    st.success(f"✅ {result['message']}")
                else:
                    stato_msg = "contabilizzato" if calcola_stato_movimento(data_movimento.strftime("%Y-%m-%d")) == "contabilizzata" else "pianificato"
                    st.success(f"✅ Movimento {stato_msg} con successo!")
                st.rerun()
            else:
                st.error(f"❌ Errore: {result['error']}")



# ============================================
# VISTA: CONTI (Invariata)
# ============================================

def mostra_conti():
    """Gestione conti e trasferimenti"""
    st.title("💳 Gestione Conti")
    
    user_id = st.session_state.user.id
    conti_mgr = ContiManager(st.session_state.supabase, user_id)
    
    tab1, tab2, tab3 = st.tabs(["📊 I Miei Conti", "💸 Trasferimenti", "🔧 Gestione"])
    
    with tab1:
        mostra_lista_conti(conti_mgr)
    
    with tab2:
        mostra_trasferimenti()
    
    with tab3:
        mostra_gestione_conti(conti_mgr)


def mostra_lista_conti(conti_mgr):
    """Lista conti con saldi"""
    conti = conti_mgr.get_conti()
    
    if not conti:
        st.info("Nessun conto trovato. Creane uno nella sezione Gestione.")
        return
    
    for conto in conti:
        with st.expander(f"💳 {conto['nome'].upper()}", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            saldo = conti_mgr.get_saldo_conto(conto['id'])
            
            with col1:
                st.metric("Saldo Attuale", f"€ {saldo:,.2f}")
            
            with col2:
                st.metric("Tipo", conto['tipo'].capitalize())
            
            with col3:
                st.metric("Valuta", conto['valuta'])
            
            with st.form(f"rettifica_{conto['id']}"):
                col_r1, col_r2, col_r3 = st.columns([2, 2, 1])
                
                with col_r1:
                    saldo_reale = st.number_input("Saldo Reale (€)", value=float(saldo), step=0.01, key=f"saldo_{conto['id']}")
                
                with col_r2:
                    motivo = st.text_input("Motivo rettifica", key=f"motivo_{conto['id']}")
                
                with col_r3:
                    if st.form_submit_button("🔧 Rettifica"):
                        result = conti_mgr.rettifica_saldo(conto['id'], saldo_reale, motivo)
                        
                        if result["success"]:
                            if "message" in result:
                                st.info(result["message"])
                            else:
                                st.success(f"✅ Saldo rettificato! Differenza: € {result['differenza']:,.2f}")
                                st.rerun()
                        else:
                            st.error(f"❌ {result['error']}")


def mostra_trasferimenti():
    """Form trasferimenti con PIN"""
    user_id = st.session_state.user.id
    conti_mgr = ContiManager(st.session_state.supabase, user_id)
    trasf_mgr = TrasferimentiManager(st.session_state.supabase, user_id)
    token_mgr = TokenManager(st.session_state.supabase, user_id)
    
    st.subheader("💸 Trasferisci Fondi tra Conti")
    
    conti = conti_mgr.get_conti()
    if len(conti) < 2:
        st.warning("Devi avere almeno 2 conti per effettuare trasferimenti")
        return
    
    with st.form("form_trasferimento"):
        conti_dict = {c['nome']: c['id'] for c in conti}
        
        col1, col2 = st.columns(2)
        
        with col1:
            conto_origine = st.selectbox("Da Conto", list(conti_dict.keys()))
            importo = st.number_input("Importo (€)", min_value=0.01, step=0.01)
        
        with col2:
            conto_dest = st.selectbox("A Conto", [c for c in conti_dict.keys() if c != conto_origine])
            descrizione = st.text_input("Descrizione (opzionale)")
        
        genera_pin = st.form_submit_button("🔐 Genera PIN")
        
        if genera_pin:
            pin = token_mgr.genera_pin(durata_minuti=5)
            st.success(f"✅ PIN generato: **{pin}**\n\nValido per 5 minuti")
            st.session_state.pin_generato = True
    
    if st.session_state.get("pin_generato", False):
        with st.form("conferma_trasferimento"):
            pin_input = st.text_input("Inserisci PIN", type="password", max_chars=6)
            conferma = st.form_submit_button("✅ Conferma Trasferimento", type="primary")
            
            if conferma:
                if not pin_input:
                    st.error("Inserisci il PIN")
                elif not token_mgr.verifica_pin(pin_input):
                    st.error("❌ PIN non valido o scaduto")
                else:
                    result = trasf_mgr.trasferisci(
                        importo=importo,
                        conto_origine_id=conti_dict[conto_origine],
                        conto_destinazione_id=conti_dict[conto_dest],
                        descrizione=descrizione
                    )
                    
                    if result["success"]:
                        st.success("✅ Trasferimento completato!")
                        st.session_state.pin_generato = False
                        st.rerun()
                    else:
                        st.error(f"❌ {result['error']}")
    
    st.divider()
    
    st.subheader("📜 Storico Trasferimenti")
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        data_da = st.date_input("Dal", value=datetime.now() - timedelta(days=30))
    with col_f2:
        data_a = st.date_input("Al", value=datetime.now())
    
    trasferimenti = trasf_mgr.get_trasferimenti(
        data_inizio=data_da.strftime("%Y-%m-%d"),
        data_fine=data_a.strftime("%Y-%m-%d")
    )
    
    if trasferimenti:
        trasf_display = []
        for t in trasferimenti:
            trasf_display.append({
                "Data": t['data'],
                "Da": t['conto_origine_nome'],
                "A": t['conto_destinazione_nome'],
                "Importo": f"€ {t['importo']:,.2f}",
                "Descrizione": t['descrizione'] or "-"
            })
        
        st.dataframe(pd.DataFrame(trasf_display), use_container_width=True, hide_index=True)
    else:
        st.info("Nessun trasferimento nel periodo selezionato")


def mostra_gestione_conti(conti_mgr):
    """Gestione conti: crea, modifica, elimina"""
    st.subheader("🔧 Gestione Conti")
    
    with st.expander("➕ Crea Nuovo Conto"):
        with st.form("form_nuovo_conto"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                nome = st.text_input("Nome Conto*")
            
            with col2:
                tipo = st.selectbox("Tipo", ["principale", "deposito", "investimento", "altro"])
            
            with col3:
                saldo_iniziale = st.number_input("Saldo Iniziale (€)", value=0.0, step=0.01)
            
            submitted = st.form_submit_button("➕ Crea Conto")
            
            if submitted:
                if not nome:
                    st.error("Inserisci un nome per il conto")
                else:
                    result = conti_mgr.aggiungi_conto(nome, tipo, saldo_iniziale)
                    
                    if result["success"]:
                        st.success(f"✅ Conto '{nome}' creato!")
                        st.rerun()
                    else:
                        st.error(f"❌ {result['error']}")
    
    st.divider()
    
    conti = conti_mgr.get_conti(solo_attivi=False)
    
    if conti:
        st.write("📋 **Conti Esistenti:**")
        
        for conto in conti:
            with st.expander(f"{'✅' if conto['attivo'] else '❌'} {conto['nome']}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Tipo:** {conto['tipo']}")
                    st.write(f"**Stato:** {'Attivo' if conto['attivo'] else 'Disattivato'}")
                
                with col2:
                    if conto['attivo']:
                        if st.button(f"🚫 Disattiva", key=f"dis_{conto['id']}"):
                            conti_mgr.disattiva_conto(conto['id'])
                            st.success("Conto disattivato")
                            st.rerun()
                    else:
                        if st.button(f"✅ Riattiva", key=f"att_{conto['id']}"):
                            conti_mgr.modifica_conto(conto['id'], attivo=True)
                            st.success("Conto riattivato")
                            st.rerun()


# ============================================
# VISTA: STATISTICHE (Invariata dal precedente)
# ============================================

def mostra_statistiche():
    """Grafici e statistiche avanzate"""
    st.title("📈 Statistiche e Analisi")
    
    user_id = st.session_state.user.id
    stats_mgr = StatisticheManager(st.session_state.supabase, user_id)
    
    st.subheader("📊 Trend Ultimi 12 Mesi")
    
    trend = stats_mgr.trend_mensile(12)
    trend_df = pd.DataFrame(trend)
    
    fig_trend_12 = go.Figure()
    
    fig_trend_12.add_trace(go.Scatter(
        x=trend_df['nome_mese'],
        y=trend_df['entrate_effettive'],
        mode='lines+markers',
        name='Entrate',
        line=dict(color='#10b981', width=3),
        fill='tonexty'
    ))
    
    fig_trend_12.add_trace(go.Scatter(
        x=trend_df['nome_mese'],
        y=trend_df['uscite_effettive'],
        mode='lines+markers',
        name='Uscite',
        line=dict(color='#ef4444', width=3),
        fill='tozeroy'
    ))
    
    fig_trend_12.update_layout(
        hovermode='x unified',
        height=400,
        yaxis_title="Euro (€)"
    )
    
    st.plotly_chart(fig_trend_12, use_container_width=True)
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💸 Top Uscite per Categoria")
        
        anno_stats = datetime.now().year
        cat_stats = stats_mgr.statistiche_per_categoria(anno_stats)
        uscite_top = [c for c in cat_stats if c['tipo'] == 'uscita'][:10]
        
        if uscite_top:
            fig_top_uscite = px.bar(
                pd.DataFrame(uscite_top),
                x='importo_totale',
                y='categoria',
                orientation='h',
                color='importo_totale',
                color_continuous_scale='Reds',
                height=400
            )
            
            fig_top_uscite.update_layout(showlegend=False, xaxis_title="Euro (€)", yaxis_title="")
            
            st.plotly_chart(fig_top_uscite, use_container_width=True)
    
    with col2:
        st.subheader("💰 Fonti di Entrata")
        
        entrate_top = [c for c in cat_stats if c['tipo'] == 'entrata'][:10]
        
        if entrate_top:
            fig_entrate = px.pie(
                pd.DataFrame(entrate_top),
                values='importo_totale',
                names='categoria',
                hole=0.4,
                height=400,
                color_discrete_sequence=px.colors.sequential.Greens_r
            )
            
            st.plotly_chart(fig_entrate, use_container_width=True)


# ============================================
# VISTA: IMPOSTAZIONI (Invariata dal precedente)
# ============================================

def mostra_impostazioni():
    """Impostazioni utente e categorie"""
    st.title("⚙️ Impostazioni")
    
    user_id = st.session_state.user.id
    cat_mgr = CategorieManager(st.session_state.supabase, user_id)
    mov_mgr = MovimentiManager(st.session_state.supabase, user_id)
    
    tab1, tab2, tab3 = st.tabs(["🎨 Categorie", "🔄 Aggiornamenti", "👤 Account"])
    
    with tab1:
        st.subheader("Gestione Categorie")
        
        with st.expander("➕ Nuova Categoria"):
            with st.form("form_categoria"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    nome_cat = st.text_input("Nome")
                
                with col2:
                    tipo_cat = st.selectbox("Tipo", ["entrata", "uscita"])
                
                with col3:
                    colore_cat = st.color_picker("Colore", "#6366f1")
                
                if st.form_submit_button("Aggiungi"):
                    result = cat_mgr.aggiungi_categoria(nome_cat, tipo_cat, colore_cat)
                    
                    if result["success"]:
                        st.success("✅ Categoria aggiunta!")
                        st.rerun()
                    else:
                        st.error(f"❌ {result['error']}")
        
        st.divider()
        
        col_e, col_u = st.columns(2)
        
        with col_e:
            st.write("**💚 Categorie Entrate:**")
            entrate = cat_mgr.get_categorie(tipo="entrata")
            
            for cat in entrate:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"🎨 {cat['nome']}")
                with col2:
                    if st.button("🗑️", key=f"del_e_{cat['id']}"):
                        cat_mgr.elimina_categoria(cat['id'])
                        st.rerun()
        
        with col_u:
            st.write("**💔 Categorie Uscite:**")
            uscite = cat_mgr.get_categorie(tipo="uscita")
            
            for cat in uscite:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"🎨 {cat['nome']}")
                with col2:
                    if st.button("🗑️", key=f"del_u_{cat['id']}"):
                        cat_mgr.elimina_categoria(cat['id'])
                        st.rerun()
    
    with tab2:
        st.subheader("🔄 Aggiornamento Automatico Stati")
        
        st.info("""
        **Come funziona:**
        - I movimenti pianificati vengono automaticamente contabilizzati quando arriva la loro data
        - L'aggiornamento avviene automaticamente ad ogni accesso all'app
        - Puoi anche forzare l'aggiornamento manualmente con il pulsante qui sotto
        """)
        
        # Mostra movimenti pianificati in scadenza
        oggi = datetime.now().date()
        movimenti_pianificati = mov_mgr.get_movimenti(stato="pianificata", includi_pianificati=True)
        
        # Filtra solo quelli con data <= oggi
        movimenti_scaduti = [m for m in movimenti_pianificati if datetime.strptime(m['data'], "%Y-%m-%d").date() <= oggi]
        
        if movimenti_scaduti:
            st.warning(f"⚠️ Ci sono {len(movimenti_scaduti)} movimenti pianificati da contabilizzare:")
            
            for mov in movimenti_scaduti[:5]:  # Mostra max 5
                st.write(f"• {mov['data']} - {mov['descrizione']} - € {mov['importo']:,.2f}")
            
            if len(movimenti_scaduti) > 5:
                st.write(f"... e altri {len(movimenti_scaduti) - 5}")
        else:
            st.success("✅ Nessun movimento pianificato in scadenza")
        
        st.divider()
        
        # Pulsante aggiornamento manuale
        col_upd1, col_upd2 = st.columns([1, 3])
        
        with col_upd1:
            if st.button("🔄 Aggiorna Ora", type="primary", use_container_width=True):
                result = mov_mgr.aggiorna_stati_automatico()
                
                if result["success"]:
                    if result["aggiornati"] > 0:
                        st.success(f"✅ {result['aggiornati']} movimento/i aggiornato/i a contabilizzato!")
                        
                        with st.expander("📋 Dettaglio movimenti aggiornati"):
                            for desc in result["movimenti"]:
                                st.write(f"• {desc}")
                        
                        st.rerun()
                    else:
                        st.info("ℹ️ Nessun movimento da aggiornare")
                else:
                    st.error(f"❌ Errore: {result['error']}")
        
        with col_upd2:
            st.caption("Clicca per forzare l'aggiornamento di tutti i movimenti pianificati con data passata")
        
        st.divider()
        
        # Statistiche movimenti pianificati
        st.subheader("📊 Statistiche Movimenti Pianificati")
        
        movimenti_pianificati_tutti = mov_mgr.get_movimenti(stato="pianificata", includi_pianificati=True)
        
        if movimenti_pianificati_tutti:
            col_stat1, col_stat2, col_stat3 = st.columns(3)
            
            with col_stat1:
                st.metric("📅 Totale Pianificati", len(movimenti_pianificati_tutti))
            
            with col_stat2:
                importo_totale = sum(float(m['importo']) for m in movimenti_pianificati_tutti)
                st.metric("💰 Importo Totale", f"€ {importo_totale:,.2f}")
            
            with col_stat3:
                prossimo = min(movimenti_pianificati_tutti, key=lambda x: x['data'])
                data_prossimo = datetime.strptime(prossimo['data'], "%Y-%m-%d")
                giorni_mancanti = (data_prossimo.date() - oggi).days
                st.metric("⏱️ Prossimo tra", f"{giorni_mancanti} giorni" if giorni_mancanti > 0 else "Oggi!")
        else:
            st.info("Nessun movimento pianificato al momento")
    
    with tab3:
        st.subheader("👤 Account")
        
        if st.session_state.user:
            st.info(f"📧 Email: {st.session_state.user.email}")
        
        st.divider()
        
        if st.button("🚪 Logout", type="primary"):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.rerun()


# ============================================
# MAIN APP
# ============================================

def main():
    """Applicazione principale"""
    
    if not st.session_state.logged_in:
        mostra_login()
        return
    
    auth_mgr = AuthManager(st.session_state.supabase)
    user = auth_mgr.get_current_user()
    
    if not user:
        st.session_state.logged_in = False
        st.rerun()
    
    st.session_state.user = user
    
    user_id = st.session_state.user.id
    mov_mgr = MovimentiManager(st.session_state.supabase, user_id)
    mov_mgr.aggiorna_stati_automatico()

    mostra_sidebar()
    
    if st.session_state.vista_corrente == "dashboard":
        mostra_dashboard()
    elif st.session_state.vista_corrente == "movimenti":
        mostra_movimenti()
    elif st.session_state.vista_corrente == "conti":
        mostra_conti()
    elif st.session_state.vista_corrente == "statistiche":
        mostra_statistiche()
    elif st.session_state.vista_corrente == "impostazioni":
        mostra_impostazioni()


if __name__ == "__main__":
    main()