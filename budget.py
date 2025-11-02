#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backend per gestione finanze personali
Integrazione con Supabase
"""

import os
import secrets
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import Dict, List, Optional, Tuple
from supabase import create_client, Client
import streamlit as st
import calendar

# ============================================
# CONFIGURAZIONE SUPABASE
# ============================================

def get_supabase_client() -> Client:
    """
    Crea client Supabase usando credenziali da environment o Streamlit secrets
    """
    try:
        url = "https://erspnrawliyphfhuxkrv.supabase.co"
        key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVyc3BucmF3bGl5cGhmaHV4a3J2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjAzODA0MDQsImV4cCI6MjA3NTk1NjQwNH0.7FLoqfubttJwxifqYr13pCZXXSiUDIS-xJ6E8NvKA0A"
    except:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        raise ValueError("Credenziali Supabase non trovate. Configura secrets.toml o environment variables.")
    
    return create_client(url, key)


# ============================================
# UTILITY - VALIDAZIONE DATE
# ============================================

def valida_data(anno: int, mese: int, giorno: int) -> datetime.date:
    """
    Valida e corregge una data, gestendo giorni non validi
    """
    # Trova l'ultimo giorno del mese
    ultimo_giorno = calendar.monthrange(anno, mese)[1]
    
    # Se il giorno richiesto è maggiore dell'ultimo giorno valido, usa l'ultimo giorno
    giorno_valido = min(giorno, ultimo_giorno)
    
    return datetime(anno, mese, giorno_valido).date()


def calcola_stato_movimento(data_movimento: str) -> str:
    """
    Determina lo stato del movimento in base alla data
    - Data <= oggi → contabilizzata
    - Data > oggi → pianificata
    """
    data_mov = datetime.strptime(data_movimento, "%Y-%m-%d").date()
    oggi = datetime.now().date()
    
    return "contabilizzata" if data_mov <= oggi else "pianificata"


# ============================================
# AUTENTICAZIONE
# ============================================

class AuthManager:
    """Gestisce autenticazione utenti"""
    
    def __init__(self, supabase: Client):
        self.supabase = supabase
    
    def login(self, email: str, password: str) -> Dict:
        """Login utente"""
        try:
            response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            return {"success": True, "user": response.user, "session": response.session}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def register(self, email: str, password: str) -> Dict:
        """Registrazione nuovo utente"""
        try:
            response = self.supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            return {"success": True, "user": response.user}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def logout(self):
        """Logout utente"""
        try:
            self.supabase.auth.sign_out()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_current_user(self):
        """Recupera utente corrente"""
        try:
            user = self.supabase.auth.get_user()
            return user.user if user else None
        except:
            return None


# ============================================
# GESTIONE CATEGORIE
# ============================================

class CategorieManager:
    """Gestisce categorie entrate/uscite"""
    
    def __init__(self, supabase: Client, user_id: str):
        self.supabase = supabase
        self.user_id = user_id
    
    def get_categorie(self, tipo: Optional[str] = None) -> List[Dict]:
        """Recupera categorie utente"""
        query = self.supabase.table("categorie").select("*").eq("user_id", self.user_id)
        
        if tipo:
            query = query.eq("tipo", tipo)
        
        result = query.order("nome").execute()
        return result.data or []
    
    def aggiungi_categoria(self, nome: str, tipo: str, colore: str = "#6366f1") -> Dict:
        """Aggiungi nuova categoria"""
        try:
            result = self.supabase.table("categorie").insert({
                "user_id": self.user_id,
                "nome": nome,
                "tipo": tipo,
                "colore": colore
            }).execute()
            return {"success": True, "data": result.data[0]}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def elimina_categoria(self, categoria_id: int) -> Dict:
        """Elimina categoria"""
        try:
            self.supabase.table("categorie").delete().eq("id", categoria_id).eq("user_id", self.user_id).execute()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def inizializza_categorie_default(self):
        """Crea categorie di default per nuovo utente"""
        categorie_default = [
            ("Stipendio", "entrata", "#10b981"),
            ("Freelance", "entrata", "#3b82f6"),
            ("Investimenti", "entrata", "#8b5cf6"),
            ("Altro", "entrata", "#6b7280"),
            ("Alimentari", "uscita", "#ef4444"),
            ("Trasporti", "uscita", "#f59e0b"),
            ("Casa", "uscita", "#ec4899"),
            ("Bollette", "uscita", "#f97316"),
            ("Salute", "uscita", "#14b8a6"),
            ("Svago", "uscita", "#a855f7"),
            ("Shopping", "uscita", "#84cc16"),
            ("Abbonamenti", "uscita", "#06b6d4"),
            ("Altro", "uscita", "#6b7280"),
        ]
        
        for nome, tipo, colore in categorie_default:
            self.aggiungi_categoria(nome, tipo, colore)


# ============================================
# GESTIONE CONTI
# ============================================

class ContiManager:
    """Gestisce conti correnti"""
    
    def __init__(self, supabase: Client, user_id: str):
        self.supabase = supabase
        self.user_id = user_id
    
    def get_conti(self, solo_attivi: bool = True) -> List[Dict]:
        """Recupera conti utente"""
        query = self.supabase.table("conti").select("*").eq("user_id", self.user_id)
        
        if solo_attivi:
            query = query.eq("attivo", True)
        
        result = query.order("nome").execute()
        return result.data or []
    
    def get_conto(self, conto_id: int) -> Optional[Dict]:
        """Recupera singolo conto"""
        result = self.supabase.table("conti").select("*").eq("id", conto_id).eq("user_id", self.user_id).execute()
        return result.data[0] if result.data else None
    
    def aggiungi_conto(self, nome: str, tipo: str = "principale", saldo_iniziale: float = 0) -> Dict:
        """Aggiungi nuovo conto"""
        try:
            result = self.supabase.table("conti").insert({
                "user_id": self.user_id,
                "nome": nome,
                "tipo": tipo,
                "saldo_iniziale": saldo_iniziale,
                "attivo": True
            }).execute()
            return {"success": True, "data": result.data[0]}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def modifica_conto(self, conto_id: int, **kwargs) -> Dict:
        """Modifica conto esistente"""
        try:
            self.supabase.table("conti").update(kwargs).eq("id", conto_id).eq("user_id", self.user_id).execute()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def disattiva_conto(self, conto_id: int) -> Dict:
        """Disattiva conto (soft delete)"""
        return self.modifica_conto(conto_id, attivo=False)
    
    def get_saldi_conti(self) -> Dict[str, float]:
        """Calcola saldi di tutti i conti"""
        result = self.supabase.table("v_saldi_conti").select("*").eq("user_id", self.user_id).execute()
        
        saldi = {}
        totale = 0
        
        for conto in result.data or []:
            saldi[conto["conto_nome"]] = float(conto["saldo_attuale"])
            totale += float(conto["saldo_attuale"])
        
        saldi["TOTALE"] = totale
        return saldi
    
    def get_saldo_conto(self, conto_id: int) -> float:
        """Calcola saldo singolo conto"""
        result = self.supabase.rpc("calcola_saldo_conto", {"p_conto_id": conto_id}).execute()
        return float(result.data) if result.data else 0.0
    
    def rettifica_saldo(self, conto_id: int, saldo_reale: float, motivo: str = "") -> Dict:
        """Rettifica saldo conto creando movimento di compensazione"""
        try:
            saldo_attuale = self.get_saldo_conto(conto_id)
            differenza = saldo_reale - saldo_attuale
            
            if abs(differenza) < 0.01:
                return {"success": True, "message": "Nessuna rettifica necessaria"}
            
            tipo = "entrata" if differenza > 0 else "uscita"
            importo = abs(differenza)
            
            movimento_result = MovimentiManager(self.supabase, self.user_id).aggiungi_movimento(
                data=datetime.now().strftime("%Y-%m-%d"),
                descrizione=f"Rettifica saldo{': ' + motivo if motivo else ''}",
                importo=importo,
                categoria_nome="Rettifica saldo",
                tipo=tipo,
                conto_id=conto_id
            )
            
            if not movimento_result["success"]:
                return movimento_result
            
            self.supabase.table("rettifiche_saldo").insert({
                "user_id": self.user_id,
                "conto_id": conto_id,
                "saldo_precedente": saldo_attuale,
                "saldo_reale": saldo_reale,
                "differenza": differenza,
                "motivo": motivo,
                "movimento_id": movimento_result["data"]["id"]
            }).execute()
            
            return {"success": True, "differenza": differenza, "movimento": movimento_result["data"]}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def inizializza_conti_default(self):
        """Crea conti di default per nuovo utente"""
        self.aggiungi_conto("Principale", "principale", 0)
        self.aggiungi_conto("Deposito", "deposito", 0)


# ============================================
# GESTIONE MOVIMENTI
# ============================================

class MovimentiManager:
    """Gestisce movimenti finanziari"""
    
    def __init__(self, supabase: Client, user_id: str):
        self.supabase = supabase
        self.user_id = user_id
    
    def get_movimenti(self, 
                     data_inizio: Optional[str] = None,
                     data_fine: Optional[str] = None,
                     conto_id: Optional[int] = None,
                     categoria_id: Optional[int] = None,
                     tipo: Optional[str] = None,
                     stato: Optional[str] = None,
                     includi_pianificati: bool = True) -> List[Dict]:
        """Recupera movimenti con filtri"""
        query = self.supabase.table("movimenti")\
            .select("*, categorie(nome, colore), conti(nome)")\
            .eq("user_id", self.user_id)
        
        if data_inizio:
            query = query.gte("data", data_inizio)
        if data_fine:
            query = query.lte("data", data_fine)
        if conto_id:
            query = query.eq("conto_id", conto_id)
        if categoria_id:
            query = query.eq("categoria_id", categoria_id)
        if tipo:
            query = query.eq("tipo", tipo)
        if stato:
            query = query.eq("stato", stato)
        elif not includi_pianificati:
            query = query.eq("stato", "contabilizzata")
        
        result = query.order("data", desc=True).execute()
        return result.data or []
    
    def get_movimento(self, movimento_id: int) -> Optional[Dict]:
        """Recupera singolo movimento"""
        result = self.supabase.table("movimenti").select("*").eq("id", movimento_id).eq("user_id", self.user_id).execute()
        return result.data[0] if result.data else None
    
    def aggiungi_movimento(self,
                          data: str,
                          descrizione: str,
                          importo: float,
                          categoria_nome: str,
                          tipo: str,
                          conto_id: int,
                          periodico: bool = False,
                          numero_rate: Optional[int] = None,
                          data_inizio: Optional[str] = None,
                          note: Optional[str] = None) -> Dict:
        """
        Aggiungi movimento (una tantum o periodico con rate)
        
        Se periodico=True:
        - Crea TUTTE le rate immediatamente
        - Rate con data <= oggi → contabilizzate
        - Rate con data > oggi → pianificate
        """
        try:
            # Recupera o crea categoria
            cat_mgr = CategorieManager(self.supabase, self.user_id)
            categorie = cat_mgr.get_categorie(tipo=tipo)
            categoria = next((c for c in categorie if c["nome"] == categoria_nome), None)
            
            if not categoria:
                cat_result = cat_mgr.aggiungi_categoria(categoria_nome, tipo)
                if not cat_result["success"]:
                    return cat_result
                categoria = cat_result["data"]
            
            movimenti_creati = []
            
            if periodico and numero_rate and data_inizio:
                # MODALITÀ PERIODICA: Crea tutte le rate
                data_inizio_obj = datetime.strptime(data_inizio, "%Y-%m-%d").date()
                
                for i in range(numero_rate):
                    # Calcola data della rata (mensile)
                    data_rata_obj = data_inizio_obj + relativedelta(months=i)
                    
                    # Valida la data (gestisce 31 in mesi con 30 giorni)
                    data_rata_obj = valida_data(
                        data_rata_obj.year,
                        data_rata_obj.month,
                        data_inizio_obj.day
                    )
                    
                    data_rata_str = data_rata_obj.strftime("%Y-%m-%d")
                    
                    # Determina stato in base alla data
                    stato = calcola_stato_movimento(data_rata_str)
                    
                    # Crea movimento
                    movimento_data = {
                        "user_id": self.user_id,
                        "conto_id": conto_id,
                        "categoria_id": categoria["id"],
                        "data": data_rata_str,
                        "descrizione": f"{descrizione} (Rata {i+1}/{numero_rate})",
                        "importo": abs(float(importo)),
                        "tipo": tipo,
                        "stato": stato,
                        "periodico": True,
                        "frequenza": "mensile",
                        "data_inizio": data_inizio,
                        "note": note
                    }
                    
                    result = self.supabase.table("movimenti").insert(movimento_data).execute()
                    movimenti_creati.append(result.data[0])
                
                return {
                    "success": True,
                    "data": movimenti_creati,
                    "message": f"Create {numero_rate} rate ({sum(1 for m in movimenti_creati if m['stato'] == 'contabilizzata')} contabilizzate, {sum(1 for m in movimenti_creati if m['stato'] == 'pianificata')} pianificate)"
                }
            
            else:
                # MODALITÀ UNA TANTUM
                # Determina stato in base alla data
                stato = calcola_stato_movimento(data)
                
                movimento_data = {
                    "user_id": self.user_id,
                    "conto_id": conto_id,
                    "categoria_id": categoria["id"],
                    "data": data,
                    "descrizione": descrizione,
                    "importo": abs(float(importo)),
                    "tipo": tipo,
                    "stato": stato,
                    "periodico": False,
                    "note": note
                }
                
                result = self.supabase.table("movimenti").insert(movimento_data).execute()
                return {"success": True, "data": result.data[0]}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def modifica_movimento(self, movimento_id: int, **kwargs) -> Dict:
        """Modifica movimento esistente"""
        try:
            if "importo" in kwargs:
                kwargs["importo"] = abs(float(kwargs["importo"]))
            
            # Se cambio la data, ricalcola lo stato
            if "data" in kwargs:
                kwargs["stato"] = calcola_stato_movimento(kwargs["data"])
            
            self.supabase.table("movimenti").update(kwargs).eq("id", movimento_id).eq("user_id", self.user_id).execute()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def elimina_movimento(self, movimento_id: int) -> Dict:
        """
        Elimina movimento e aggiorna saldo se era contabilizzato
        """
        try:
            # Recupera movimento prima di eliminarlo
            movimento = self.get_movimento(movimento_id)
            
            if not movimento:
                return {"success": False, "error": "Movimento non trovato"}
            
            # Elimina dal database
            self.supabase.table("movimenti").delete().eq("id", movimento_id).eq("user_id", self.user_id).execute()
            
            return {
                "success": True,
                "era_contabilizzato": movimento["stato"] == "contabilizzata",
                "importo": movimento["importo"],
                "tipo": movimento["tipo"]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def elimina_rate_periodiche(self, descrizione_base: str, conto_id: int) -> Dict:
        """
        Elimina tutte le rate di un movimento periodico
        """
        try:
            # Trova tutte le rate con la stessa descrizione base
            movimenti = self.get_movimenti(conto_id=conto_id)
            movimenti_da_eliminare = [
                m for m in movimenti 
                if descrizione_base in m["descrizione"] and m["periodico"]
            ]
            
            eliminati = 0
            for mov in movimenti_da_eliminare:
                result = self.elimina_movimento(mov["id"])
                if result["success"]:
                    eliminati += 1
            
            return {"success": True, "eliminati": eliminati}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def aggiorna_stati_automatico(self) -> Dict:
        """
        Aggiorna automaticamente i movimenti pianificati a contabilizzati
        quando la data è arrivata (data <= oggi)
        
        Questa funzione dovrebbe essere eseguita:
        - All'avvio dell'app
        - Ad ogni cambio pagina
        - Manualmente tramite pulsante
        """
        try:
            oggi = datetime.now().date()
            
            # Trova tutti i movimenti pianificati con data <= oggi
            movimenti_da_aggiornare = self.supabase.table("movimenti")\
                .select("id, data, descrizione")\
                .eq("user_id", self.user_id)\
                .eq("stato", "pianificata")\
                .lte("data", oggi.strftime("%Y-%m-%d"))\
                .execute()
            
            aggiornati = 0
            
            for mov in movimenti_da_aggiornare.data or []:
                # Aggiorna stato a contabilizzata
                self.supabase.table("movimenti")\
                    .update({"stato": "contabilizzata"})\
                    .eq("id", mov["id"])\
                    .eq("user_id", self.user_id)\
                    .execute()
                
                aggiornati += 1
            
            return {
                "success": True,
                "aggiornati": aggiornati,
                "movimenti": [m["descrizione"] for m in (movimenti_da_aggiornare.data or [])]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}


# ============================================
# GESTIONE TRASFERIMENTI
# ============================================

class TrasferimentiManager:
    """Gestisce trasferimenti tra conti"""
    
    def __init__(self, supabase: Client, user_id: str):
        self.supabase = supabase
        self.user_id = user_id
    
    def trasferisci(self, 
                   importo: float,
                   conto_origine_id: int,
                   conto_destinazione_id: int,
                   descrizione: str = "",
                   data: Optional[str] = None) -> Dict:
        """Esegui trasferimento tra conti"""
        try:
            if importo <= 0:
                return {"success": False, "error": "Importo deve essere positivo"}
            
            if conto_origine_id == conto_destinazione_id:
                return {"success": False, "error": "Impossibile trasferire allo stesso conto"}
            
            conti_mgr = ContiManager(self.supabase, self.user_id)
            saldo_origine = conti_mgr.get_saldo_conto(conto_origine_id)
            
            if saldo_origine < importo:
                return {"success": False, "error": "Saldo insufficiente nel conto origine"}
            
            conto_origine = conti_mgr.get_conto(conto_origine_id)
            conto_dest = conti_mgr.get_conto(conto_destinazione_id)
            
            if not conto_origine or not conto_dest:
                return {"success": False, "error": "Conto non trovato"}
            
            data_trasf = data or datetime.now().strftime("%Y-%m-%d")
            mov_mgr = MovimentiManager(self.supabase, self.user_id)
            
            desc_uscita = descrizione or f"Trasferimento a {conto_dest['nome']}"
            mov_uscita = mov_mgr.aggiungi_movimento(
                data=data_trasf,
                descrizione=desc_uscita,
                importo=importo,
                categoria_nome="Trasferimento",
                tipo="uscita",
                conto_id=conto_origine_id
            )
            
            if not mov_uscita["success"]:
                return mov_uscita
            
            desc_entrata = descrizione or f"Trasferimento da {conto_origine['nome']}"
            mov_entrata = mov_mgr.aggiungi_movimento(
                data=data_trasf,
                descrizione=desc_entrata,
                importo=importo,
                categoria_nome="Trasferimento",
                tipo="entrata",
                conto_id=conto_destinazione_id
            )
            
            if not mov_entrata["success"]:
                mov_mgr.elimina_movimento(mov_uscita["data"]["id"])
                return mov_entrata
            
            self.supabase.table("trasferimenti").insert({
                "user_id": self.user_id,
                "conto_origine_id": conto_origine_id,
                "conto_destinazione_id": conto_destinazione_id,
                "importo": importo,
                "data": data_trasf,
                "descrizione": descrizione,
                "movimento_uscita_id": mov_uscita["data"]["id"],
                "movimento_entrata_id": mov_entrata["data"]["id"]
            }).execute()
            
            return {"success": True, "uscita": mov_uscita["data"], "entrata": mov_entrata["data"]}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_trasferimenti(self, data_inizio: Optional[str] = None, data_fine: Optional[str] = None) -> List[Dict]:
        """Recupera storico trasferimenti"""
        query = self.supabase.table("trasferimenti")\
            .select("id, data, importo, descrizione, conto_origine_id, conto_destinazione_id, created_at")\
            .eq("user_id", self.user_id)
        
        if data_inizio:
            query = query.gte("data", data_inizio)
        if data_fine:
            query = query.lte("data", data_fine)
        
        result = query.order("data", desc=True).execute()
        
        trasferimenti = result.data or []
        conti_mgr = ContiManager(self.supabase, self.user_id)
        
        for trasf in trasferimenti:
            conto_origine = conti_mgr.get_conto(trasf['conto_origine_id'])
            conto_dest = conti_mgr.get_conto(trasf['conto_destinazione_id'])
            trasf['conto_origine_nome'] = conto_origine['nome'] if conto_origine else 'Sconosciuto'
            trasf['conto_destinazione_nome'] = conto_dest['nome'] if conto_dest else 'Sconosciuto'
        
        return trasferimenti


# ============================================
# GESTIONE TOKEN PIN
# ============================================

class TokenManager:
    """Gestisce token temporanei per operazioni sicure"""
    
    def __init__(self, supabase: Client, user_id: str):
        self.supabase = supabase
        self.user_id = user_id
    
    def genera_pin(self, durata_minuti: int = 5) -> str:
        """Genera PIN temporaneo per trasferimenti"""
        pin = f"{secrets.randbelow(1000000):06d}"
        scadenza = datetime.now() + timedelta(minutes=durata_minuti)
        
        self.supabase.table("token_temporanei").insert({
            "user_id": self.user_id,
            "token": pin,
            "tipo": "pin_trasferimento",
            "scadenza": scadenza.isoformat()
        }).execute()
        
        return pin
    
    def verifica_pin(self, pin: str) -> bool:
        """Verifica validità PIN"""
        result = self.supabase.table("token_temporanei")\
            .select("*")\
            .eq("user_id", self.user_id)\
            .eq("token", pin)\
            .eq("tipo", "pin_trasferimento")\
            .eq("usato", False)\
            .gte("scadenza", datetime.now().isoformat())\
            .execute()
        
        if not result.data:
            return False
        
        token_id = result.data[0]["id"]
        self.supabase.table("token_temporanei").update({"usato": True}).eq("id", token_id).execute()
        
        return True


# ============================================
# STATISTICHE E RIEPILOGHI
# ============================================

class StatisticheManager:
    """Genera statistiche e riepiloghi"""
    
    def __init__(self, supabase: Client, user_id: str):
        self.supabase = supabase
        self.user_id = user_id
    
    def riepilogo_mensile(self, anno: int, mese: int, conto_id: Optional[int] = None) -> Dict:
        """
        Riepilogo mensile entrate/uscite
        Include sia movimenti contabilizzati che pianificati
        """
        mov_mgr = MovimentiManager(self.supabase, self.user_id)
        
        data_inizio = f"{anno}-{mese:02d}-01"
        ultimo_giorno = calendar.monthrange(anno, mese)[1]
        data_fine = f"{anno}-{mese:02d}-{ultimo_giorno:02d}"
        
        # Recupera tutti i movimenti del mese (contabilizzati e pianificati)
        movimenti = mov_mgr.get_movimenti(
            data_inizio=data_inizio,
            data_fine=data_fine,
            conto_id=conto_id,
            includi_pianificati=True
        )
        
        entrate_effettive = 0
        uscite_effettive = 0
        entrate_previste = 0
        uscite_previste = 0
        num_movimenti = 0
        
        for mov in movimenti:
            importo = float(mov["importo"])
            
            if mov["stato"] == "contabilizzata":
                if mov["tipo"] == "entrata":
                    entrate_effettive += importo
                else:
                    uscite_effettive += importo
                num_movimenti += 1
            elif mov["stato"] == "pianificata":
                if mov["tipo"] == "entrata":
                    entrate_previste += importo
                else:
                    uscite_previste += importo
        
        return {
            "entrate_effettive": entrate_effettive,
            "uscite_effettive": uscite_effettive,
            "entrate_previste": entrate_previste,
            "uscite_previste": uscite_previste,
            "bilancio_effettivo": entrate_effettive - uscite_effettive,
            "bilancio_previsto": entrate_previste - uscite_previste,
            "num_movimenti": num_movimenti
        }
    
    def riepilogo_annuale(self, anno: int) -> Dict:
        """Riepilogo annuale con dati per ogni mese"""
        mesi_data = []
        
        for mese in range(1, 13):
            riepilogo = self.riepilogo_mensile(anno, mese)
            riepilogo["mese"] = mese
            riepilogo["nome_mese"] = datetime(anno, mese, 1).strftime("%B")
            mesi_data.append(riepilogo)
        
        totale_entrate = sum(m["entrate_effettive"] for m in mesi_data)
        totale_uscite = sum(m["uscite_effettive"] for m in mesi_data)
        
        return {
            "anno": anno,
            "mesi": mesi_data,
            "totale_entrate": totale_entrate,
            "totale_uscite": totale_uscite,
            "bilancio_annuale": totale_entrate - totale_uscite
        }
    
    def statistiche_per_categoria(self, anno: int, mese: Optional[int] = None) -> List[Dict]:
        """Statistiche raggruppate per categoria (solo contabilizzate)"""
        mov_mgr = MovimentiManager(self.supabase, self.user_id)
        
        data_inizio = f"{anno}-{mese:02d}-01" if mese else f"{anno}-01-01"
        ultimo_giorno = calendar.monthrange(anno, mese)[1] if mese else 31
        data_fine = f"{anno}-{mese:02d}-{ultimo_giorno:02d}" if mese else f"{anno}-12-31"
        
        movimenti = mov_mgr.get_movimenti(
            data_inizio=data_inizio,
            data_fine=data_fine,
            stato="contabilizzata"  # Solo movimenti effettivi
        )
        
        categorie_stats = {}
        
        for mov in movimenti:
            cat_nome = mov["categorie"]["nome"] if mov["categorie"] else "Senza categoria"
            
            if cat_nome not in categorie_stats:
                categorie_stats[cat_nome] = {
                    "categoria": cat_nome,
                    "tipo": mov["tipo"],
                    "importo_totale": 0,
                    "num_movimenti": 0,
                    "colore": mov["categorie"]["colore"] if mov["categorie"] else "#6b7280"
                }
            
            categorie_stats[cat_nome]["importo_totale"] += float(mov["importo"])
            categorie_stats[cat_nome]["num_movimenti"] += 1
        
        return sorted(categorie_stats.values(), key=lambda x: x["importo_totale"], reverse=True)
    
    def trend_mensile(self, num_mesi: int = 12) -> List[Dict]:
        """Trend ultimi N mesi"""
        oggi = datetime.now()
        trend = []
        
        for i in range(num_mesi - 1, -1, -1):
            data = oggi - relativedelta(months=i)
            riepilogo = self.riepilogo_mensile(data.year, data.month)
            riepilogo["anno"] = data.year
            riepilogo["mese"] = data.month
            riepilogo["nome_mese"] = data.strftime("%b %Y")
            trend.append(riepilogo)
        
        return trend

