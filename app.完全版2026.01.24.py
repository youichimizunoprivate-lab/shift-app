# app.py
import streamlit as st
import streamlit.components.v1 as components
import os
import json
import time
import datetime
import calendar
import hashlib
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from typing import Optional, Iterator

import pandas as pd
from ortools.sat.python import cp_model
import locale



try:
    locale.setlocale(locale.LC_ALL, 'ja_JP.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, '')
    except:
        pass

try:
    import jpholiday
except Exception:
    jpholiday = None


# ----------------------------
# Page Config & Google-like (Material-ish) CSS
# ----------------------------
st.set_page_config(
    page_title="Shift App",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Streamlit compatibility
if not hasattr(st, "rerun"):
    st.rerun = st.experimental_rerun

# Google Apps-like Styling (simple, readable, color used only for emphasis)
st.markdown(
    """
<style>
:root{
  --bg:#F8F9FA;
  --surface:#FFFFFF;
  --text:#202124;
  --sub:#5F6368;
  --line:#E0E3E7;

  --blue:#1A73E8;
  --green:#34A853;
  --yellow:#FBBC05;
  --red:#EA4335;
  --orange:#FA7B17;

  --r16:16px;
  --r12:12px;
  --shadow: 0 1px 2px rgba(60,64,67,.15), 0 1px 3px rgba(60,64,67,.10);
}

.stApp { background-color: var(--bg); color: var(--text); }
.main .block-container{
  padding-top: 1.25rem;
  padding-bottom: 6rem;
  max-width: 680px;
}

h1,h2,h3,h4{ font-family: -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; color:var(--text); }
small, .stCaption { color: var(--sub) !important; }

.card{
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r16);
  padding: 14px 14px;
  box-shadow: var(--shadow);
  margin-bottom: 12px;
}
/* Fix for st.container(border=True) to match card style */
div[data-testid="stVerticalBlockBorderWrapper"]{
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r16);
  padding: 14px 14px;
  box-shadow: var(--shadow);
  margin-bottom: 12px;
}
.card-title{
  font-weight: 800;
  font-size: 15px;
  margin: 0 0 10px 0;
  display:flex;
  align-items:center;
  gap:8px;
  flex-wrap: wrap;
}
.badge{
  display:inline-flex;
  align-items:center;
  gap:6px;
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid var(--line);
  background: #F1F3F4;
  color: var(--text);
}
.badge.blue{ background: rgba(26,115,232,.10); border-color: rgba(26,115,232,.20); color: var(--blue); }
.badge.red{ background: rgba(234,67,53,.10); border-color: rgba(234,67,53,.20); color: var(--red); }
.badge.green{ background: rgba(52,168,83,.10); border-color: rgba(52,168,83,.20); color: var(--green); }
.badge.orange{ background: rgba(250,123,23,.10); border-color: rgba(250,123,23,.20); color: var(--orange); }
.badge.yellow{ background: rgba(251,188,5,.15); border-color: rgba(251,188,5,.25); color: #F9A825; }

.stButton > button{
  border-radius: var(--r12);
  font-weight: 800;
  height: 44px;
  border: 1px solid var(--line);
  background: var(--surface);
  box-shadow: none;
  transition: transform .05s ease;
  white-space: pre-line;
  color: var(--text);
}
.stButton > button:hover {
  background-color: rgba(26,115,232,0.1);
  border-color: var(--blue);
  color: var(--blue);
}
.stButton > button:active { transform: scale(0.98); }

.stTextInput input, .stSelectbox div[data-baseweb="select"]{
  border-radius: 12px !important;
}
hr{ border-color: var(--line); }

/* Counter UI */
.counter-row{
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:10px;
  padding: 10px 12px;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: #FDFDFD;
}
.counter-label{
  font-weight: 800;
  color: var(--text);
}
.counter-val{
  min-width: 44px;
  text-align:center;
  font-weight: 900;
  font-size: 16px;
  padding: 6px 10px;
  border-radius: 12px;
  background:#F1F3F4;
  border:1px solid var(--line);
}
/* Staff list action buttons */
div[data-testid="stHorizontalBlock"]:has(.staff-row-marker) .stButton > button{
  height: 72px !important;
  min-height: 72px !important;
  font-size: 18px !important;
  font-weight: 900 !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  padding: 0 !important;
}
div[data-testid="stHorizontalBlock"]:has(.staff-row-marker){
  align-items: flex-start !important;
  margin-bottom: 8px !important;
}
div[data-testid="stHorizontalBlock"]:has(.staff-row-marker) > div{
  padding-top: 0 !important;
  padding-bottom: 0 !important;
}
div[data-testid="stHorizontalBlock"]:has(.staff-row-marker) .stButton{
  margin: 0 !important;
}
div[data-testid="stHorizontalBlock"]:has(.staff-row-marker) .staff-card{
  margin: 0 !important;
  transform: translateY(-12px);
}
div[data-testid="column"]:has(.staff-row-marker) div[data-testid="stMarkdown"]{
  margin-top: 0 !important;
  margin-bottom: 0 !important;
}
/* Staff detail basic settings counters */
div[data-testid="stVerticalBlockBorderWrapper"]:has(#sd-basic-marker) .counter-val{
  background:#E8F0FE;
  border-color:#AECBFA;
  color:#1A73E8;
  font-size:18px;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(#sd-basic-marker) .counter-label{
  color:#1A73E8;
  font-weight:900;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(#sd-basic-marker) .stButton > button{
  background:#E8F0FE;
  border-color:#AECBFA;
  color:#1A73E8;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(#sd-basic-marker) .stButton > button:hover{
  background:#D2E3FC;
  border-color:#8AB4F8;
  color:#1A73E8;
}
#sd-basic-title{
  font-size: 26px !important;
  font-weight: 900 !important;
}
#sd-pc-title{
  font-size: 26px !important;
  font-weight: 900 !important;
}
.sd-hol-caption{
  font-weight: 900 !important;
  font-size: 22px !important;
  color: #202124 !important;
  margin: 8px 0 10px !important;
}
.sd-pc-caption{
  font-weight: 800 !important;
  font-size: 16px !important;
  color: #202124 !important;
  margin: 6px 0 10px !important;
}
/* Provisional editor readability */
#provisional-editor-marker ~ div[data-testid="stDataFrame"] {
  font-size: 15px !important;
}
#provisional-editor-marker ~ div[data-testid="stDataFrame"] [role="gridcell"] {
  padding: 8px 6px !important;
}
#provisional-editor-marker ~ div[data-testid="stDataFrame"] input,
#provisional-editor-marker ~ div[data-testid="stDataFrame"] select {
  font-size: 15px !important;
  height: 36px !important;
}

/* Red button for Delete Exceptions (via marker) */
div:has(#btn-delete-exceptions) + div button:hover {
  background-color: rgba(234,67,53,0.1);
  border-color: var(--red);
  color: var(--red);
}
div[data-testid="stMarkdown"]:has(#btn-delete-exceptions) { display: none; }

/* ========================================================== */
/* Moved from page_home: Specific Styling for Tags & Cards    */
/* ========================================================== */

/* Hide the marker markdown elements */
#ws-marker,
#hol-marker,
#trans-marker,
#global-rule-marker,
#emp-marker,
#order-marker {
    display: none !important;
}

/* ========================================================== */
/* Specific Styling for Tags & Cards (Refined Selectors)      */
/* ========================================================== */

/* 1. Employment Types (Yellow) */
div[data-testid="stVerticalBlockBorderWrapper"]:has(#card-title-emp) *[data-baseweb="tag"] {
    background-color: #FFF9C4 !important;
    border: 1px solid #FFF59D !important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(#card-title-emp) *[data-baseweb="tag"] span {
    color: #F57F17 !important;
}
@supports selector(:has(*)) {
  div[data-baseweb="select"]:has(input[aria-label*="登録済み雇用形態"]) *[data-baseweb="tag"] {
      background-color: #FFF9C4 !important;
      border: 1px solid #FFF59D !important;
  }
  div[data-baseweb="select"]:has(input[aria-label*="登録済み雇用形態"]) *[data-baseweb="tag"] span {
      color: #F57F17 !important;
  }
}
#emp-tags *[data-baseweb="tag"] {
    background-color: #FFF9C4 !important;
    border: 1px solid #FFF59D !important;
}
#emp-tags *[data-baseweb="tag"] span {
    color: #F57F17 !important;
}
#emp-marker ~ div div[data-baseweb="select"]:has(input[aria-label*="登録済み雇用形態"]) *[data-baseweb="tag"] {
    background-color: #FFF9C4 !important;
    border: 1px solid #FFF59D !important;
}
#emp-marker ~ div div[data-baseweb="select"]:has(input[aria-label*="登録済み雇用形態"]) *[data-baseweb="tag"] span {
    color: #F57F17 !important;
}
#emp-marker ~ div *[data-baseweb="tag"] {
    background-color: #FFF9C4 !important;
    border: 1px solid #FFF59D !important;
}
#emp-marker ~ div *[data-baseweb="tag"] span {
    color: #F57F17 !important;
}
div[id*="emp_multiselect_editor"] *[data-baseweb="tag"] {
    background-color: #FFF9C4 !important;
    border: 1px solid #FFF59D !important;
}
div[id*="emp_multiselect_editor"] *[data-baseweb="tag"] span {
    color: #F57F17 !important;
}

/* 2. Work Shifts (Blue) */
div[data-testid="stVerticalBlockBorderWrapper"]:has(#card-title-ws) *[data-baseweb="tag"] {
    background-color: rgba(26,115,232,.20) !important;
    border: 1px solid rgba(26,115,232,.30) !important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(#card-title-ws) *[data-baseweb="tag"] span {
    color: #1A73E8 !important;
}
@supports selector(:has(*)) {
  div[data-baseweb="select"]:has(input[aria-label*="登録済み担務"]) *[data-baseweb="tag"] {
      background-color: rgba(26,115,232,.20) !important;
      border: 1px solid rgba(26,115,232,.30) !important;
  }
  div[data-baseweb="select"]:has(input[aria-label*="登録済み担務"]) *[data-baseweb="tag"] span {
      color: #1A73E8 !important;
  }
}
#ws-tags *[data-baseweb="tag"] {
    background-color: rgba(26,115,232,.20) !important;
    border: 1px solid rgba(26,115,232,.30) !important;
}
#ws-tags *[data-baseweb="tag"] span {
    color: #1A73E8 !important;
}
#ws-marker ~ div div[data-baseweb="select"]:has(input[aria-label*="登録済み担務"]) *[data-baseweb="tag"] {
    background-color: rgba(26,115,232,.20) !important;
    border: 1px solid rgba(26,115,232,.30) !important;
}
#ws-marker ~ div div[data-baseweb="select"]:has(input[aria-label*="登録済み担務"]) *[data-baseweb="tag"] span {
    color: #1A73E8 !important;
}
#ws-marker ~ div *[data-baseweb="tag"] {
    background-color: rgba(26,115,232,.20) !important;
    border: 1px solid rgba(26,115,232,.30) !important;
}
#ws-marker ~ div *[data-baseweb="tag"] span {
    color: #1A73E8 !important;
}
div[id*="ws_multiselect_editor"] *[data-baseweb="tag"] {
    background-color: rgba(26,115,232,.20) !important;
    border: 1px solid rgba(26,115,232,.30) !important;
}
div[id*="ws_multiselect_editor"] *[data-baseweb="tag"] span {
    color: #1A73E8 !important;
}

/* 3. Holidays (Light Red) */
div[data-testid="stVerticalBlockBorderWrapper"]:has(#card-title-hol) *[data-baseweb="tag"],
div[data-testid="stVerticalBlockBorderWrapper"]:has(#card-title-hol-detail) *[data-baseweb="tag"],
div[data-testid="stVerticalBlockBorderWrapper"]:has(#card-title-hol-public) *[data-baseweb="tag"],
div[data-testid="stVerticalBlockBorderWrapper"]:has(#card-title-hol-priority) *[data-baseweb="tag"] {
    background-color: rgba(234, 67, 53, 0.15) !important;
    border: 1px solid rgba(234, 67, 53, 0.25) !important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(#card-title-hol) *[data-baseweb="tag"] span,
div[data-testid="stVerticalBlockBorderWrapper"]:has(#card-title-hol-detail) *[data-baseweb="tag"] span,
div[data-testid="stVerticalBlockBorderWrapper"]:has(#card-title-hol-public) *[data-baseweb="tag"] span,
div[data-testid="stVerticalBlockBorderWrapper"]:has(#card-title-hol-priority) *[data-baseweb="tag"] span {
    color: #D32F2F !important;
}
@supports selector(:has(*)) {
  div[data-baseweb="select"]:has(input[aria-label*="登録済み休日"]) *[data-baseweb="tag"],
  div[data-baseweb="select"]:has(input[aria-label*="登録済みルール"]) *[data-baseweb="tag"],
  div[data-baseweb="select"]:has(input[aria-label*="登録済み順序ルール"]) *[data-baseweb="tag"] {
      background-color: rgba(234, 67, 53, 0.15) !important;
      border: 1px solid rgba(234, 67, 53, 0.25) !important;
  }
  div[data-baseweb="select"]:has(input[aria-label*="登録済み休日"]) *[data-baseweb="tag"] span,
  div[data-baseweb="select"]:has(input[aria-label*="登録済みルール"]) *[data-baseweb="tag"] span,
  div[data-baseweb="select"]:has(input[aria-label*="登録済み順序ルール"]) *[data-baseweb="tag"] span {
      color: #D32F2F !important;
  }
  div[data-baseweb="select"]:has(input[aria-label*="登録済みルール"]) *[data-baseweb="tag"],
  div[data-baseweb="select"]:has(input[aria-label*="登録済みルール"]) *[data-baseweb="tag"] span {
      white-space: normal !important;
      max-width: none !important;
  }
  div[data-baseweb="select"]:has(input[aria-label*="登録済み順序ルール"]) *[data-baseweb="tag"],
  div[data-baseweb="select"]:has(input[aria-label*="登録済み順序ルール"]) *[data-baseweb="tag"] span {
      white-space: normal !important;
      max-width: none !important;
  }
}
#hol-tags *[data-baseweb="tag"],
#gr-tags *[data-baseweb="tag"],
#order-tags *[data-baseweb="tag"] {
    background-color: rgba(234, 67, 53, 0.15) !important;
    border: 1px solid rgba(234, 67, 53, 0.25) !important;
}
#hol-tags *[data-baseweb="tag"] span,
#gr-tags *[data-baseweb="tag"] span,
#order-tags *[data-baseweb="tag"] span {
    color: #D32F2F !important;
}
#hol-marker ~ div div[data-baseweb="select"]:has(input[aria-label*="登録済み休日"]) *[data-baseweb="tag"],
#global-rule-marker ~ div div[data-baseweb="select"]:has(input[aria-label*="登録済みルール"]) *[data-baseweb="tag"],
#order-marker ~ div div[data-baseweb="select"]:has(input[aria-label*="登録済み順序ルール"]) *[data-baseweb="tag"] {
    background-color: rgba(234, 67, 53, 0.15) !important;
    border: 1px solid rgba(234, 67, 53, 0.25) !important;
}
#hol-marker ~ div div[data-baseweb="select"]:has(input[aria-label*="登録済み休日"]) *[data-baseweb="tag"] span,
#global-rule-marker ~ div div[data-baseweb="select"]:has(input[aria-label*="登録済みルール"]) *[data-baseweb="tag"] span,
#order-marker ~ div div[data-baseweb="select"]:has(input[aria-label*="登録済み順序ルール"]) *[data-baseweb="tag"] span {
    color: #D32F2F !important;
}
#hol-marker ~ div *[data-baseweb="tag"],
#global-rule-marker ~ div *[data-baseweb="tag"],
#order-marker ~ div *[data-baseweb="tag"] {
    background-color: rgba(234, 67, 53, 0.15) !important;
    border: 1px solid rgba(234, 67, 53, 0.25) !important;
}
#hol-marker ~ div *[data-baseweb="tag"] span,
#global-rule-marker ~ div *[data-baseweb="tag"] span,
#order-marker ~ div *[data-baseweb="tag"] span {
    color: #D32F2F !important;
}
div[id*="hol_multiselect_editor"] *[data-baseweb="tag"],
div[id*="gr_multiselect"] *[data-baseweb="tag"],
div[id*="order_multiselect"] *[data-baseweb="tag"] {
    background-color: rgba(234, 67, 53, 0.15) !important;
    border: 1px solid rgba(234, 67, 53, 0.25) !important;
}
div[id*="hol_multiselect_editor"] *[data-baseweb="tag"] span,
div[id*="gr_multiselect"] *[data-baseweb="tag"] span,
div[id*="order_multiselect"] *[data-baseweb="tag"] span {
    color: #D32F2F !important;
}

/* 4. Prohibited Transitions (Purple) */
div[data-testid="stVerticalBlockBorderWrapper"]:has(#card-title-ng) *[data-baseweb="tag"] {
    background-color: rgba(156, 39, 176, 0.20) !important;
    border: 1px solid rgba(156, 39, 176, 0.30) !important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(#card-title-ng) *[data-baseweb="tag"] span {
    color: #9C27B0 !important;
}
@supports selector(:has(*)) {
  div[data-baseweb="select"]:has(input[aria-label*="登録済み禁止パターン"]) *[data-baseweb="tag"] {
      background-color: rgba(156, 39, 176, 0.20) !important;
      border: 1px solid rgba(156, 39, 176, 0.30) !important;
  }
  div[data-baseweb="select"]:has(input[aria-label*="登録済み禁止パターン"]) *[data-baseweb="tag"] span {
      color: #9C27B0 !important;
  }
}
@supports selector(:has(*)) {
  div[data-baseweb="select"]:has(input[aria-label*="登録済みシフト"]) *[data-baseweb="tag"],
  div[data-baseweb="select"]:has(input[aria-label*="登録済みシフト"]) *[data-baseweb="tag"] span {
      white-space: normal !important;
      max-width: none !important;
  }
}
#trans-tags *[data-baseweb="tag"] {
    background-color: rgba(156, 39, 176, 0.20) !important;
    border: 1px solid rgba(156, 39, 176, 0.30) !important;
}
#trans-tags *[data-baseweb="tag"] span {
    color: #9C27B0 !important;
}
#trans-marker ~ div div[data-baseweb="select"]:has(input[aria-label*="登録済み禁止パターン"]) *[data-baseweb="tag"] {
    background-color: rgba(156, 39, 176, 0.20) !important;
    border: 1px solid rgba(156, 39, 176, 0.30) !important;
}
#trans-marker ~ div div[data-baseweb="select"]:has(input[aria-label*="登録済み禁止パターン"]) *[data-baseweb="tag"] span {
    color: #9C27B0 !important;
}
#trans-marker ~ div *[data-baseweb="tag"] {
    background-color: rgba(156, 39, 176, 0.20) !important;
    border: 1px solid rgba(156, 39, 176, 0.30) !important;
}
#trans-marker ~ div *[data-baseweb="tag"] span {
    color: #9C27B0 !important;
}
div[id*="trans_multiselect"] *[data-baseweb="tag"] {
    background-color: rgba(156, 39, 176, 0.20) !important;
    border: 1px solid rgba(156, 39, 176, 0.30) !important;
}
div[id*="trans_multiselect"] *[data-baseweb="tag"] span {
    color: #9C27B0 !important;
}

/* 5. Global Rules (Light Red) - via Marker */
div[data-testid="stMarkdown"]:has(#global-rule-marker) ~ div *[data-baseweb="tag"] {
    background-color: rgba(234, 67, 53, 0.15) !important;
    border: 1px solid rgba(234, 67, 53, 0.25) !important;
}
div[data-testid="stMarkdown"]:has(#global-rule-marker) ~ div *[data-baseweb="tag"] span {
    color: #D32F2F !important;
}

/* Toggle Switch Custom Color (Blue) */
div[data-testid="stToggle"] input:checked + div {
    background-color: #1A73E8 !important;
}

/* カード内の入力欄やボタンの背景を白くして見やすくする補正 */
div[data-testid="stVerticalBlockBorderWrapper"]:has(.card-title) .stTextInput input,
div[data-testid="stVerticalBlockBorderWrapper"]:has(.card-title) .stSelectbox div[data-baseweb="select"],
div[data-testid="stVerticalBlockBorderWrapper"]:has(.card-title) button {
    background-color: #FFFFFF !important;
}


</style>
""",
    unsafe_allow_html=True,
)

# Safari-compatible tag coloring via parent DOM injection from a component iframe.
components.html(
    """
<script>
(() => {
  const parentDoc = window.parent && window.parent.document;
  if (!parentDoc) return;

  const rules = [
    { label: "登録済み雇用形態", cls: "tag-emp" },
    { label: "登録済み担務", cls: "tag-ws" },
    { label: "登録済み休日", cls: "tag-hol" },
    { label: "登録済みルール", cls: "tag-hol" },
    { label: "登録済み順序ルール", cls: "tag-hol" },
    { label: "登録済み禁止パターン", cls: "tag-ng" },
  ];

  const addStyles = () => {
    if (parentDoc.getElementById("tag-color-style")) return;
    const style = parentDoc.createElement("style");
    style.id = "tag-color-style";
    style.textContent = `
      .tag-emp { background-color: #FFF9C4 !important; border: 1px solid #FFF59D !important; }
      .tag-emp span { color: #F57F17 !important; }
      .tag-ws { background-color: rgba(26,115,232,.20) !important; border: 1px solid rgba(26,115,232,.30) !important; }
      .tag-ws span { color: #1A73E8 !important; }
      .tag-hol { background-color: rgba(234, 67, 53, 0.15) !important; border: 1px solid rgba(234, 67, 53, 0.25) !important; }
      .tag-hol span { color: #D32F2F !important; }
      .tag-ng { background-color: rgba(156, 39, 176, 0.20) !important; border: 1px solid rgba(156, 39, 176, 0.30) !important; }
      .tag-ng span { color: #9C27B0 !important; }
    `;
    parentDoc.head.appendChild(style);
  };

  const apply = () => {
    rules.forEach(({ label, cls }) => {
      const inputs = parentDoc.querySelectorAll(`input[aria-label*="${label}"]`);
      inputs.forEach((input) => {
        const root = input.closest('[data-baseweb="select"]') || input.parentElement;
        if (!root) return;
        root.querySelectorAll('[data-baseweb="tag"]').forEach((tag) => {
          tag.classList.add(cls);
        });
      });
    });
  };

  const boot = () => {
    addStyles();
    apply();
    const obs = new MutationObserver(() => apply());
    obs.observe(parentDoc.body, { childList: true, subtree: true });
  };

  boot();
})();
</script>
""",
    height=0,
    width=0,
)


# ----------------------------
# Constants & Helpers
# ----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USER_DATA_DIR = os.path.join(BASE_DIR, "user_data")
os.makedirs(USER_DATA_DIR, exist_ok=True)

SOLVER_TIMEOUT = 300
WEEKDAYS_JP = ["月", "火", "水", "木", "金", "土", "日"]


def read_df_from_json(data):
    if isinstance(data, dict) and {"data", "index", "columns"} <= set(data.keys()):
        return pd.DataFrame(data["data"], index=data["index"], columns=data["columns"])
    if isinstance(data, str) and data.strip():
        return pd.read_json(data, orient="split")
    return pd.DataFrame()


def df_to_json_dict(df: pd.DataFrame) -> dict:
    return json.loads(df.to_json(orient="split", force_ascii=False))


def safe_int(v, default=0):
    if pd.isna(v):
        return default
    try:
        return int(v)
    except Exception:
        return default


def serialize_time(v):
    if isinstance(v, datetime.time):
        return v.strftime("%H:%M")
    return v


def compute_days(start: datetime.date, end: datetime.date):
    """days(list[str]), day_map(dict[str, date])"""
    date_range = []
    cur = start
    while cur <= end:
        date_range.append(cur)
        cur += datetime.timedelta(days=1)

    days = []
    for d in date_range:
        w = WEEKDAYS_JP[d.weekday()]
        days.append(f"{d.month}/{d.day}({w})")
    day_map = {d_str: d_obj for d_str, d_obj in zip(days, date_range)}
    return days, day_map


def badge_class_for_weekday(wd: str) -> str:
    if wd == "土":
        return "blue"
    if wd == "日":
        return "orange"
    return "green"


def badge_class_for_daylabel(day_label: str) -> str:
    if jpholiday and "day_map" in st.session_state:
        d = st.session_state["day_map"].get(day_label)
        try:
            if d and jpholiday.is_holiday(d):
                return "orange"
        except:
            pass
    if "(土)" in day_label:
        return "blue"
    if "(日)" in day_label:
        return "orange"
    return "green"


def render_shift_table_html(df: pd.DataFrame, for_export: bool = False) -> str:
    hol_types = st.session_state.get("holiday_types_list", [])
    day_map = st.session_state.get("day_map", {})

    # HTMLテーブル構築（ヘッダーの色付けを確実にするため）
    th_list = []
    for col in df.columns:
        c_style = ""
        is_holiday_flag = False
        if jpholiday and col in day_map:
            try:
                if jpholiday.is_holiday(day_map[col]):
                    is_holiday_flag = True
            except:
                pass

        if "(土)" in str(col):
            c_style = "color: #1A73E8;"
        elif "(日)" in str(col) or is_holiday_flag:
            c_style = "color: #EA4335;"
        
        # スタッフ名カラムは固定
        extra_th = ""
        if col == "スタッフ名" and not for_export:
            extra_th = "position:sticky; left:0; background:#F8F9FA; z-index:2;"
        
        th_list.append(f'<th style="{c_style} min-width:40px; {extra_th}">{col}</th>')
    
    thead = f"<thead><tr>{''.join(th_list)}</tr></thead>"
    
    tbody_rows = []
    for _, row in df.iterrows():
        td_list = []
        for col in df.columns:
            val = row[col]
            td_style = ""
            extra_td = ""
            
            if col == "スタッフ名":
                if not for_export:
                    extra_td = "text-align:left; font-weight:bold; position:sticky; left:0; background:#fff; z-index:1;"
                else:
                    extra_td = "text-align:left; font-weight:bold;"
            else:
                if val in hol_types or str(val).strip() == "休み(全般)":
                    td_style = "color: #EA4335; font-weight: bold;"
            
            td_list.append(f'<td style="{td_style} {extra_td}">{val}</td>')
        tbody_rows.append(f"<tr>{''.join(td_list)}</tr>")
    
    if for_export:
        table_html = f"""
        <table style="width:100%; border-collapse: collapse; font-size:13px; white-space: nowrap; border: 1px solid #E0E3E7;">
            <style>
                table th {{ background: #F8F9FA; padding: 8px; border: 1px solid #E0E3E7; font-weight: bold; }}
                table td {{ padding: 8px; border: 1px solid #E0E3E7; text-align: center; }}
            </style>
            {thead}
            <tbody>{''.join(tbody_rows)}</tbody>
        </table>
        """
    else:
        table_html = f"""
        <div style="overflow-x: auto; max-height: 600px; border: 1px solid #E0E3E7; border-radius: 8px; margin-bottom: 1rem;">
            <table style="width:100%; border-collapse: separate; border-spacing: 0; font-size:13px; white-space: nowrap;">
                <style>
                    table th {{ background: #F8F9FA; padding: 8px; border-bottom: 1px solid #E0E3E7; border-right: 1px solid #E0E3E7; font-weight: bold; position: sticky; top: 0; z-index: 1; }}
                    table td {{ padding: 8px; border-bottom: 1px solid #E0E3E7; border-right: 1px solid #E0E3E7; text-align: center; }}
                    table tr:last-child td {{ border-bottom: none; }}
                    table th:last-child, table td:last-child {{ border-right: none; }}
                </style>
                {thead}
                <tbody>{''.join(tbody_rows)}</tbody>
            </table>
        </div>
        """
    return table_html


def format_schedule_for_line(df: pd.DataFrame) -> str:
    """LINE共有用のテキスト形式を作成する"""
    if "スタッフ名" not in df.columns:
        return "エラー: スタッフ名が見つかりません"

    days = [c for c in df.columns if c != "スタッフ名"]
    hol_types = st.session_state.get("holiday_types_list", [])
    ws_order = st.session_state.get("work_shifts_list", [])

    lines = []
    lines.append("【シフト表】")

    for d in days:
        lines.append(f"\n■ {d}")
        day_shifts = {}

        for _, row in df.iterrows():
            s_name = str(row["スタッフ名"]).strip()
            if not s_name: continue
            
            val = str(row[d]).strip()
            if not val: continue
            
            # 休日以外のみ表示（勤務のみ）
            if val not in hol_types:
                if val not in day_shifts:
                    day_shifts[val] = []
                day_shifts[val].append(s_name)
        
        if not day_shifts:
            lines.append(" (勤務者なし)")
        else:
            # 表示順序のソート
            sorted_keys = sorted(day_shifts.keys(), key=lambda x: ws_order.index(x) if x in ws_order else 999)
            for s_type in sorted_keys:
                names = "、".join(day_shifts[s_type])
                lines.append(f" {s_type}: {names}")

    return "\n".join(lines)


def build_provisional_table(
    days: list[str],
    day_map: dict[str, datetime.date],
    staff_df: pd.DataFrame,
    hope_df: pd.DataFrame,
    rules_df: pd.DataFrame,
) -> pd.DataFrame:
    staff_names = [
        str(x).strip()
        for x in staff_df.get("スタッフ名", pd.Series(dtype=str)).fillna("").tolist()
        if str(x).strip()
    ]
    if rules_df is None or rules_df.empty:
        rules_df = pd.DataFrame(columns=["スタッフ名", "曜日", "希望内容", "ルールタイプ"])

    rows = []
    for s in staff_names:
        row = {"スタッフ名": s}
        rules = rules_df[(rules_df["スタッフ名"] == s) & (rules_df["ルールタイプ"] == "固定")]
        for d in days:
            val = ""
            if s in hope_df.index and d in hope_df.columns:
                v = str(hope_df.at[s, d]).strip()
                if v:
                    val = v
            if not val and not rules.empty and d in day_map:
                wd = WEEKDAYS_JP[day_map[d].weekday()]
                rule_row = rules[rules["曜日"] == wd]
                if rule_row.empty:
                    rule_row = rules[rules["曜日"] == "全日"]
                if not rule_row.empty:
                    val = str(rule_row.iloc[0]["希望内容"]).strip()
            row[d] = val
        rows.append(row)

    return pd.DataFrame(rows, columns=["スタッフ名"] + days)


def counter_input(
    label: str,
    value: int,
    key: str,
    label_size: str = "1.0rem",
    max_value: Optional[int] = None,
) -> int:
    """Mobile-friendly counter: no keyboard. Uses +/- buttons + a value pill."""
    value = int(value) if value is not None else 0
    if max_value is not None:
        value = min(value, max_value)
    c_lab, c_min, c_val, c_plus = st.columns([3, 1, 1, 1])

    with c_lab:
        st.markdown(
            f"<div class='counter-label' style='font-size:{label_size}; height:44px; display:flex; align-items:center;'>{label}</div>",
            unsafe_allow_html=True,
        )

    minus = c_min.button("－", key=f"{key}_minus", use_container_width=True)
    plus = c_plus.button("＋", key=f"{key}_plus", use_container_width=True)

    if minus:
        value = max(0, value - 1)
    if plus:
        value = value + 1
        if max_value is not None:
            value = min(max_value, value)

    with c_val:
        st.markdown(
            f"<div class='counter-val' style='margin:0 auto; text-align:center;'>{value}</div>",
            unsafe_allow_html=True,
        )
    return value


def create_save_json() -> str:
    def serialize_props(props):
        out = []
        for p in props:
            p2 = dict(p)
            for k, v in p2.items():
                p2[k] = serialize_time(v)
            out.append(p2)
        return out

    save_data = {
        "勤務シフト一覧": st.session_state.get("work_shifts_list", []),
        "勤務シフトプロパティ": serialize_props(st.session_state.get("work_shift_properties", [])),
        "休暇種類一覧": st.session_state.get("holiday_types_list", []),
        "休暇設定プロパティ": st.session_state.get("holiday_properties", []),
        "雇用形態一覧": st.session_state.get("employment_types_list", []),
        "最大連勤数": st.session_state.get("max_consecutive_work", 5),
        "禁止シフト遷移": st.session_state.get("prohibited_transitions", []),
        "NGペア": st.session_state.get("ng_pairs", []),
        "スタッフ情報": df_to_json_dict(st.session_state["staff_df"]) if "staff_df" in st.session_state else {},
        "日別必要人数": df_to_json_dict(st.session_state["req_df"]) if "req_df" in st.session_state else {},
        "希望シフト": df_to_json_dict(st.session_state["hope_df"]) if "hope_df" in st.session_state else {},
        "曜日別必要人数": df_to_json_dict(st.session_state["req_by_weekday"]) if "req_by_weekday" in st.session_state else {},
        "個別ルール": df_to_json_dict(st.session_state["individual_rules_df"]) if "individual_rules_df" in st.session_state else {},
        "確定シフト結果": df_to_json_dict(st.session_state["last_result"])
        if st.session_state.get("last_result") is not None
        else {},
        "開始日": st.session_state.get("start_date", datetime.date.today()).isoformat(),
        "終了日": st.session_state.get("end_date", datetime.date.today()).isoformat(),
        "充填用シフト": st.session_state.get("filler_shift_type", None),
        "期間内回数": st.session_state.get("period_counts", {}),
        "共通ルール": st.session_state.get("global_rules", []),
        "休日順序ルール": st.session_state.get("holiday_order_rules", []),
        "祝日代休ルール": st.session_state.get("public_holiday_rules", {}),
    }
    return json.dumps(save_data, ensure_ascii=False, indent=2)


def load_state_from_dict(loaded: dict):
    try:
        for key, state_key in [
            ("勤務シフト一覧", "work_shifts_list"),
            ("勤務シフトプロパティ", "work_shift_properties"),
            ("休暇種類一覧", "holiday_types_list"),
            ("休暇設定プロパティ", "holiday_properties"),
            ("雇用形態一覧", "employment_types_list"),
            ("最大連勤数", "max_consecutive_work"),
            ("禁止シフト遷移", "prohibited_transitions"),
            ("NGペア", "ng_pairs"),
            ("充填用シフト", "filler_shift_type"),
            ("期間内回数", "period_counts"),
            ("共通ルール", "global_rules"),
            ("休日順序ルール", "holiday_order_rules"),
            ("祝日代休ルール", "public_holiday_rules"),
        ]:
            if key in loaded:
                st.session_state[state_key] = loaded[key]

        if "開始日" in loaded:
            try:
                st.session_state["start_date"] = datetime.date.fromisoformat(loaded["開始日"])
            except Exception:
                pass
        if "終了日" in loaded:
            try:
                st.session_state["end_date"] = datetime.date.fromisoformat(loaded["終了日"])
            except Exception:
                pass

        if "スタッフ情報" in loaded:
            df = read_df_from_json(loaded["スタッフ情報"])
            if "スタッフ名" not in df.columns and "name" in df.columns:
                df.rename(columns={"name": "スタッフ名"}, inplace=True)
            if "スタッフ名" in df.columns:
                st.session_state["staff_df"] = df.reset_index(drop=True)

        for key, state_key in [
            ("日別必要人数", "req_df"),
            ("希望シフト", "hope_df"),
            ("曜日別必要人数", "req_by_weekday"),
            ("個別ルール", "individual_rules_df"),
        ]:
            if key in loaded:
                st.session_state[state_key] = read_df_from_json(loaded[key])
    except Exception as e:
        st.error(f"データの読み込みに失敗しました: {e}")


def load_user_json(user: str):
    path = os.path.join(USER_DATA_DIR, f"{user}.json")
    if not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        load_state_from_dict(loaded)
    except Exception as e:
        st.error(f"データの読み込みに失敗しました: {e}")


def autosave_user_json(user: str):
    try:
        save_path = os.path.join(USER_DATA_DIR, f"{user}.json")
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(create_save_json())
    except Exception as e:
        st.error(f"自動保存に失敗しました: {e}")


# ----------------------------
# Sync helpers (data loss防止の要)
# ----------------------------
def ensure_core_defaults():
    if "work_shifts_list" not in st.session_state:
        st.session_state["work_shifts_list"] = ["日勤", "夜勤"]
    if "work_shift_properties" not in st.session_state:
        st.session_state["work_shift_properties"] = []
    
    # work_shifts_list と work_shift_properties の同期
    ws_props_map = {p["名称"]: p for p in st.session_state["work_shift_properties"]}
    new_ws_props = []
    for ws in st.session_state["work_shifts_list"]:
        # デフォルトは必要人数対象=True
        new_ws_props.append(ws_props_map.get(ws, {"名称": ws, "必要人数対象": True}))
    st.session_state["work_shift_properties"] = new_ws_props

    if "holiday_types_list" not in st.session_state:
        st.session_state["holiday_types_list"] = ["週休", "非番", "年休"]
    if "holiday_properties" not in st.session_state:
        st.session_state["holiday_properties"] = [
            {"名称": "週休", "週回数固定設定": True},
            {"名称": "非番", "週回数固定設定": True},
            {"名称": "年休", "週回数固定設定": False},
        ]
    if "employment_types_list" not in st.session_state:
        st.session_state["employment_types_list"] = ["正社員", "パート", "アルバイト"]
    if "max_consecutive_work" not in st.session_state:
        st.session_state["max_consecutive_work"] = 5
    if "filler_shift_type" not in st.session_state:
        # デフォルトは「年休」または休日リストの末尾（自由休日を想定）
        hol_list = st.session_state.get("holiday_types_list", [])
        if "年休" in hol_list:
            st.session_state["filler_shift_type"] = "年休"
        elif hol_list:
            st.session_state["filler_shift_type"] = hol_list[-1]
        else:
            st.session_state["filler_shift_type"] = None
    
    if "period_counts" not in st.session_state:
        st.session_state["period_counts"] = {}
    
    if "global_rules" not in st.session_state:
        st.session_state["global_rules"] = []
    
    if "holiday_order_rules" not in st.session_state:
        st.session_state["holiday_order_rules"] = []

    if "public_holiday_rules" not in st.session_state:
        st.session_state["public_holiday_rules"] = {
            "enabled": False,
            "target_employments": [],
            "comp_holiday_type": ""
        }

    if "prohibited_transitions" not in st.session_state:
        st.session_state["prohibited_transitions"] = []

    if "ng_pairs" not in st.session_state:
        st.session_state["ng_pairs"] = []
    if "individual_rules_df" not in st.session_state:
        st.session_state["individual_rules_df"] = pd.DataFrame(columns=["スタッフ名", "曜日", "希望内容", "ルールタイプ"])
    else:
        df = st.session_state["individual_rules_df"].copy()
        for c in ["スタッフ名", "曜日", "希望内容", "ルールタイプ"]:
            if c not in df.columns:
                df[c] = ""
        if "ルールタイプ" in df.columns and df["ルールタイプ"].isna().all():
            df["ルールタイプ"] = "固定"
        st.session_state["individual_rules_df"] = df

    if "staff_df" not in st.session_state:
        st.session_state["staff_df"] = pd.DataFrame(columns=["スタッフ名", "最大連勤数", "シフト開始前の連勤数"])

    if "req_df" not in st.session_state:
        st.session_state["req_df"] = pd.DataFrame()

    if "hope_df" not in st.session_state:
        st.session_state["hope_df"] = pd.DataFrame()
    if "req_by_weekday" not in st.session_state:
        st.session_state["req_by_weekday"] = pd.DataFrame()


def sync_staff_df_schema():
    """列が足りない分だけ追加。既存入力は維持。"""
    df = st.session_state["staff_df"].copy()
    if "スタッフ名" not in df.columns:
        df["スタッフ名"] = ""
    if "最大連勤数" not in df.columns:
        df["最大連勤数"] = 0
    if "前月末の連勤数" in df.columns and "シフト開始前の連勤数" not in df.columns:
        df.rename(columns={"前月末の連勤数": "シフト開始前の連勤数"}, inplace=True)
    if "シフト開始前の連勤数" not in df.columns:
        df["シフト開始前の連勤数"] = 0
    if "雇用形態" not in df.columns:
        df["雇用形態"] = ""

    work_shifts = st.session_state.get("work_shifts_list", [])
    weekly_targets = [x["名称"] for x in st.session_state.get("holiday_properties", []) if x.get("週回数固定設定")]

    for ws in work_shifts:
        if ws not in df.columns:
            df[ws] = True
        pref_col = f"{ws}希望度"
        if pref_col not in df.columns:
            df[pref_col] = "中"

    for h in weekly_targets:
        col_week = f"週の{h}日数"
        col_month = f"月の{h}日数"
        col_period = f"{h}日数対象"
        if col_week not in df.columns:
            df[col_week] = 1
        if col_month not in df.columns:
            df[col_month] = 4
        if col_period not in df.columns:
            df[col_period] = "週"

    st.session_state["staff_df"] = df.reset_index(drop=True)


def sync_req_df(days: list[str]):
    work_shifts = st.session_state.get("work_shifts_list", [])
    req_df = st.session_state["req_df"].copy()
    req_df = req_df.reindex(index=days, columns=work_shifts, fill_value=0)
    st.session_state["req_df"] = req_df


def sync_hope_df(days: list[str]):
    """hope_df を (index=スタッフ名, columns=days) に寄せる。既存入力は維持。"""
    staff_df = st.session_state["staff_df"]
    staff_names = [
        str(x).strip()
        for x in staff_df.get("スタッフ名", pd.Series(dtype=str)).fillna("").tolist()
        if str(x).strip()
    ]

    hope_df = st.session_state["hope_df"].copy()

    for d in days:
        if d not in hope_df.columns:
            hope_df[d] = ""

    for s in staff_names:
        if s not in hope_df.index:
            hope_df.loc[s] = ""

    st.session_state["hope_df"] = hope_df


# ----------------------------
# Logic / Solver
# ----------------------------
def diagnose_infeasibility(days, day_map, work_shifts, holiday_types, shift_types):
    """
    解が見つからない場合に、制約を緩和して原因を特定する診断関数
    """
    staff_df = st.session_state["staff_df"]
    hope_df = st.session_state["hope_df"]
    req_df = st.session_state["req_df"]
    
    ws_props = {p["名称"]: p for p in st.session_state.get("work_shift_properties", [])}
    target_work_shifts = [ws for ws in work_shifts if ws_props.get(ws, {}).get("必要人数対象", True)]
    
    staffs_local = [n.strip() for n in staff_df["スタッフ名"].fillna("").astype(str).tolist() if str(n).strip()]
    
    staff_settings = {}
    for _, row in staff_df.iterrows():
        name = str(row.get("スタッフ名", "")).strip()
        if not name: continue
        able = [ws for ws in work_shifts if bool(row.get(ws, False))]
        staff_settings[name] = {
            "able_shifts": able,
            "prev_consecutive_work": safe_int(row.get("シフト開始前の連勤数"), 0),
            "max_consecutive_work": safe_int(row.get("最大連勤数"), 0),
        }

    model = cp_model.CpModel()
    shift = {}
    
    # 変数定義
    for s in staffs_local:
        for d in days:
            for t in shift_types:
                shift[(s, d, t)] = model.NewBoolVar(f"shift_{s}_{d}_{t}")
            model.Add(sum(shift[(s, d, t)] for t in shift_types) == 1)

    # 可能なシフト（これは物理的な制約としてHardのままにする）
    for d in days:
        for s in staffs_local:
            able = set(staff_settings.get(s, {}).get("able_shifts", []))
            for ws in target_work_shifts:
                if ws not in able:
                    model.Add(shift[(s, d, ws)] == 0)

    violation_vars = []
    violation_msgs = []

    # 1. 希望シフト（緩和可能にする）
    for s in staffs_local:
        if s in hope_df.index:
            for d in days:
                if d in hope_df.columns:
                    val = str(hope_df.at[s, d]).strip()
                    if not val: continue
                    
                    v_var = model.NewBoolVar(f"vio_hope_{s}_{d}")
                    if val == "休み(全般)":
                        model.Add(sum(shift[(s, d, t)] for t in holiday_types) == 1).OnlyEnforceIf(v_var.Not())
                    elif val == "出勤(全般)":
                        model.Add(sum(shift[(s, d, t)] for t in work_shifts) == 1).OnlyEnforceIf(v_var.Not())
                    elif val in shift_types:
                        model.Add(shift[(s, d, val)] == 1).OnlyEnforceIf(v_var.Not())
                    
                    violation_vars.append(v_var)
                    violation_msgs.append(f"希望シフト: {s}さんの {d} ({val})")

    # 2. 個別ルール（緩和可能にする）
    rules_df = st.session_state.get("individual_rules_df", pd.DataFrame())
    if not rules_df.empty:
        for i, row in rules_df.iterrows():
            s = str(row.get("スタッフ名", "")).strip()
            dow = str(row.get("曜日", "")).strip()
            target = str(row.get("希望内容", "")).strip()
            rule_type = str(row.get("ルールタイプ", "固定")).strip()
            if s not in staffs_local: continue
            
            if dow == "全日": target_days = list(days)
            elif dow in WEEKDAYS_JP:
                idx = WEEKDAYS_JP.index(dow)
                target_days = [dd for dd in days if day_map[dd].weekday() == idx]
            else: target_days = []

            for dd in target_days:
                v_var = model.NewBoolVar(f"vio_rule_{s}_{dd}_{i}")
                if rule_type == "固定":
                    if target == "休み(全般)":
                        model.Add(sum(shift[(s, dd, t)] for t in holiday_types) == 1).OnlyEnforceIf(v_var.Not())
                    elif target == "出勤(全般)": model.Add(sum(shift[(s, dd, t)] for t in work_shifts) == 1).OnlyEnforceIf(v_var.Not())
                    elif target in shift_types: model.Add(shift[(s, dd, target)] == 1).OnlyEnforceIf(v_var.Not())
                elif rule_type == "不可":
                    if target == "休み(全般)": model.Add(sum(shift[(s, dd, t)] for t in holiday_types) == 0).OnlyEnforceIf(v_var.Not())
                    elif target == "出勤(全般)": model.Add(sum(shift[(s, dd, t)] for t in work_shifts) == 0).OnlyEnforceIf(v_var.Not())
                    elif target in shift_types: model.Add(shift[(s, dd, target)] == 0).OnlyEnforceIf(v_var.Not())
                
                violation_vars.append(v_var)
                violation_msgs.append(f"ルール: {s}さんの {dow}曜 {target} ({dd})")

    # 3. NGペア（緩和可能にする）
    for pair in st.session_state.get("ng_pairs", []):
        s1, s2 = pair.get("スタッフA"), pair.get("スタッフB")
        if s1 in staffs_local and s2 in staffs_local and s1 != s2:
            for d in days:
                v_var = model.NewBoolVar(f"vio_ng_{s1}_{s2}_{d}")
                model.Add(
                    sum(shift[(s1, d, ws)] for ws in work_shifts)
                    + sum(shift[(s2, d, ws)] for ws in work_shifts)
                    <= 1
                ).OnlyEnforceIf(v_var.Not())
                violation_vars.append(v_var)
                violation_msgs.append(f"NGペア: {s1}さんと{s2}さん ({d})")

    # 4. 連勤制限（緩和可能にする）
    global_max = int(st.session_state.get("max_consecutive_work", 5))
    for s in staffs_local:
        s_max = int(staff_settings[s].get("max_consecutive_work", 0))
        max_cons = s_max if s_max > 0 else global_max
        window_len = max_cons + 1
        
        # 開始前の連勤考慮
        prev_work = int(staff_settings[s].get("prev_consecutive_work", 0))
        if prev_work > 0:
            limit = window_len - prev_work
            if 0 < limit <= len(days):
                slack = model.NewIntVar(0, limit, f"slack_prev_{s}")
                model.Add(sum(shift[(s, d, t)] for d in days[:limit] for t in work_shifts) <= limit - 1 + slack)
                violation_vars.append(slack)
                violation_msgs.append(f"連勤制限: {s}さんの月初の連勤")

        # 期間中の連勤
        for i in range(len(days) - max_cons):
            slack = model.NewIntVar(0, window_len, f"slack_cons_{s}_{i}")
            model.Add(sum(shift[(s, d, t)] for d in days[i : i + window_len] for t in work_shifts) <= max_cons + slack)
            violation_vars.append(slack)
            violation_msgs.append(f"連勤制限: {s}さんの {days[i]} からの連勤")

    # 5. 募集なしシフト（req=0）への割り当て（緩和可能にする）
    # run_optimizationでは req=0 はHard制約のため、これが原因で解なしになる可能性がある
    for d in days:
        for ws in target_work_shifts:
            req = int(req_df.at[d, ws]) if (d in req_df.index and ws in req_df.columns) else 0
            if req == 0:
                # 募集0なのに誰かが割り当てられているかチェック
                count_var = model.NewIntVar(0, len(staffs_local), f"diag_req0_{d}_{ws}")
                model.Add(sum(shift[(s, d, ws)] for s in staffs_local) == count_var)
                v_var = model.NewBoolVar(f"vio_req0_{d}_{ws}")
                model.Add(count_var == 0).OnlyEnforceIf(v_var.Not())
                violation_vars.append(v_var)
                violation_msgs.append(f"募集なしシフト: {d} の {ws} (目標配置数0)")

    # 6. 禁止シフト遷移（緩和可能にする）
    prohibited_transitions = st.session_state.get("prohibited_transitions", [])
    for s in staffs_local:
        for i in range(len(days) - 1):
            d_curr = days[i]
            d_next = days[i+1]
            for p in prohibited_transitions:
                prev_s = p["prev"]
                next_s = p["next"]
                if prev_s in shift_types and next_s in shift_types:
                    v_var = model.NewBoolVar(f"vio_trans_{s}_{d_curr}_{prev_s}_{next_s}")
                    model.Add(shift[(s, d_curr, prev_s)] + shift[(s, d_next, next_s)] <= 1).OnlyEnforceIf(v_var.Not())
                    violation_vars.append(v_var)
                    violation_msgs.append(f"禁止遷移: {s}さんの {d_curr}({prev_s})→{d_next}({next_s})")

    # 違反の総数を最小化
    model.Minimize(sum(violation_vars))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 300.0
    status = solver.Solve(model)

    results = []
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        for var, msg in zip(violation_vars, violation_msgs):
            if solver.Value(var) > 0:
                results.append(f"・{msg} が原因で作成できません（他のルールと矛盾）。")
    return results

def run_optimization(days, day_map, work_shifts, holiday_types, shift_types):
    staff_df = st.session_state["staff_df"]
    req_df = st.session_state["req_df"]
    hope_df = st.session_state["hope_df"]

    ws_props = {p["名称"]: p for p in st.session_state.get("work_shift_properties", [])}
    target_work_shifts = [ws for ws in work_shifts if ws_props.get(ws, {}).get("必要人数対象", True)]

    staffs_local = [n.strip() for n in staff_df["スタッフ名"].fillna("").astype(str).tolist() if str(n).strip()]
    if not staffs_local:
        st.error("スタッフが登録されていません。")
        return None, []

    weekly_holiday_targets = [x["名称"] for x in st.session_state.get("holiday_properties", []) if x.get("週回数固定設定") and x.get("名称") in holiday_types]
    free_holiday_targets = [x["名称"] for x in st.session_state.get("holiday_properties", []) if not x.get("週回数固定設定") and x.get("名称") in holiday_types]

    staff_settings = {}
    for _, row in staff_df.iterrows():
        name = str(row.get("スタッフ名", "")).strip()
        if not name:
            continue
        able = [ws for ws in work_shifts if bool(row.get(ws, False))]
        holiday_counts_week = {h: safe_int(row.get(f"週の{h}日数"), 1) for h in weekly_holiday_targets}
        holiday_counts_month = {h: safe_int(row.get(f"月の{h}日数"), 4) for h in weekly_holiday_targets}
        holiday_periods = {
            h: (str(row.get(f"{h}日数対象", "週")).strip() or "週")
            for h in weekly_holiday_targets
        }
        shift_preferences = {
            ws: (str(row.get(f"{ws}希望度", "中")).strip() or "中")
            for ws in work_shifts
        }
        staff_settings[name] = {
            "able_shifts": able,
            "holiday_counts_week": holiday_counts_week,
            "holiday_counts_month": holiday_counts_month,
            "holiday_periods": holiday_periods,
            "shift_preferences": shift_preferences,
            "prev_consecutive_work": safe_int(row.get("シフト開始前の連勤数"), 0),
            "max_consecutive_work": safe_int(row.get("最大連勤数"), 0),
        }

    debug_messages = []
    # 事前チェック: 必要人数 vs 可能なスタッフ数
    for d in days:
        for ws in target_work_shifts:
            req = int(req_df.at[d, ws]) if (d in req_df.index and ws in req_df.columns) else 0
            if req > 0:
                capable = 0
                for s in staffs_local:
                    # 1. 可能なシフトに含まれているか
                    if ws not in staff_settings[s]["able_shifts"]:
                        continue
                    # 2. 希望シフトで休みや別の勤務になっていないか
                    if s in hope_df.index and d in hope_df.columns:
                        val = str(hope_df.at[s, d]).strip()
                        if val == "休み(全般)" or val in holiday_types:
                            continue
                        if val in work_shifts and val != ws:
                            continue
                    capable += 1
                if req > capable:
                    debug_messages.append(f"・{d} の「{ws}」: 目標 {req}名 に対し、勤務可能なスタッフが {capable}名 しかいません。")

    model = cp_model.CpModel()
    shift = {}
    obj_terms = []

    for s in staffs_local:
        for d in days:
            for t in shift_types:
                shift[(s, d, t)] = model.NewBoolVar(f"shift_{s}_{d}_{t}")
            model.Add(sum(shift[(s, d, t)] for t in shift_types) == 1)

    for d in days:
        for ws in target_work_shifts:
            req = int(req_df.at[d, ws]) if (d in req_df.index and ws in req_df.columns) else 0
            model.Add(sum(shift[(s, d, ws)] for s in staffs_local) == req)
            
            # 必要人数をソフト制約に変更（解なし回避のため）
            actual_var = model.NewIntVar(0, len(staffs_local), f"count_{d}_{ws}")
            model.Add(sum(shift[(s, d, ws)] for s in staffs_local) == actual_var)

            if req > 0:
                diff = model.NewIntVar(-len(staffs_local), len(staffs_local), f"diff_{d}_{ws}")
                model.Add(diff == actual_var - req)
                abs_diff = model.NewIntVar(0, len(staffs_local), f"abs_diff_{d}_{ws}")
                model.AddAbsEquality(abs_diff, diff)
                # 人数不足・過剰は大きなペナルティ
                obj_terms.append(abs_diff * -10000)
            else:
                # 必要人数0なら0人で固定（ここは厳守）
                model.Add(actual_var == 0)

    for d in days:
        for s in staffs_local:
            able = set(staff_settings.get(s, {}).get("able_shifts", []))
            for ws in target_work_shifts:
                if ws not in able:
                    model.Add(shift[(s, d, ws)] == 0)

            hope_val = ""
            if s in hope_df.index and d in hope_df.columns:
                hope_val = str(hope_df.at[s, d])

            if hope_val == "休み(全般)":
                model.Add(sum(shift[(s, d, t)] for t in holiday_types) == 1)
            elif hope_val == "出勤(全般)":
                model.Add(sum(shift[(s, d, t)] for t in work_shifts) == 1)
            elif hope_val in shift_types:
                model.Add(shift[(s, d, hope_val)] == 1)

    rules_df = st.session_state.get("individual_rules_df", pd.DataFrame())
    if not rules_df.empty:
        for _, row in rules_df.iterrows():
            s = str(row.get("スタッフ名", "")).strip()
            dow = str(row.get("曜日", "")).strip()
            target = str(row.get("希望内容", "")).strip()
            rule_type = str(row.get("ルールタイプ", "固定")).strip()
            if not s or s not in staffs_local or not dow or not target:
                continue

            if dow == "全日":
                target_days = list(days)
            elif dow in WEEKDAYS_JP:
                idx = WEEKDAYS_JP.index(dow)
                target_days = [dd for dd in days if day_map[dd].weekday() == idx]
            else:
                continue

            for dd in target_days:
                if rule_type == "固定":
                    if target == "休み(全般)":
                        model.Add(sum(shift[(s, dd, t)] for t in holiday_types) == 1)
                    elif target == "出勤(全般)":
                        model.Add(sum(shift[(s, dd, t)] for t in work_shifts) == 1)
                    elif target in shift_types:
                        model.Add(shift[(s, dd, target)] == 1)
                elif rule_type == "不可":
                    if target == "休み(全般)":
                        model.Add(sum(shift[(s, dd, t)] for t in holiday_types) == 0)
                    elif target == "出勤(全般)":
                        model.Add(sum(shift[(s, dd, t)] for t in work_shifts) == 0)
                    elif target in shift_types:
                        model.Add(shift[(s, dd, target)] == 0)

    # 共通ルール（Global Rules）
    # スタッフごとの雇用形態を取得
    staff_emp_map = {}
    if "雇用形態" in staff_df.columns:
        for _, row in staff_df.iterrows():
            nm = str(row.get("スタッフ名", "")).strip()
            em = str(row.get("雇用形態", "")).strip()
            if nm:
                staff_emp_map[nm] = em

    global_rules = st.session_state.get("global_rules", [])
    for rule in global_rules:
        r_type = rule.get("type")
        r_val = rule.get("value")
        r_shift = rule.get("shift")
        r_act = rule.get("action")
        r_emp = rule.get("employment_type")

        if not r_shift or r_shift not in shift_types:
            continue

        target_days = []
        if r_type == "dow" and r_val in WEEKDAYS_JP:
            idx = WEEKDAYS_JP.index(r_val)
            target_days = [d for d in days if day_map[d].weekday() == idx]
        elif r_type == "date" and r_val in days:
            target_days = [r_val]

        for d in target_days:
            for s in staffs_local:
                # 雇用形態によるフィルタリング
                if r_emp and r_emp != "指定なし(全員)":
                    s_emp = staff_emp_map.get(s, "")
                    if s_emp != r_emp:
                        continue

                if r_act == "禁止":
                    model.Add(shift[(s, d, r_shift)] == 0)
                elif r_act == "固定":
                    model.Add(shift[(s, d, r_shift)] == 1)
                elif r_act == "休日ならこれのみ":
                    # 指定されたシフト以外の全ての休日を禁止
                    for h in holiday_types:
                        if h != r_shift:
                            model.Add(shift[(s, d, h)] == 0)
                elif r_act.startswith("優先"):
                    # 優先設定（ソフト制約）
                    weight = 0
                    if "高" in r_act:
                        weight = 100
                    elif "中" in r_act:
                        weight = 50
                    elif "低" in r_act:
                        weight = 10
                    
                    if weight > 0:
                        obj_terms.append(shift[(s, d, r_shift)] * weight)

    for pair in st.session_state.get("ng_pairs", []):
        s1, s2 = pair.get("スタッフA"), pair.get("スタッフB")
        if s1 in staffs_local and s2 in staffs_local and s1 != s2:
            for d in days:
                model.Add(
                    sum(shift[(s1, d, ws)] for ws in work_shifts)
                    + sum(shift[(s2, d, ws)] for ws in work_shifts)
                    <= 1
                )

    prohibited_transitions = st.session_state.get("prohibited_transitions", [])
    for s in staffs_local:
        for i in range(len(days) - 1):
            d_curr = days[i]
            d_next = days[i+1]
            for p in prohibited_transitions:
                prev_s = p["prev"]
                next_s = p["next"]
                if prev_s in shift_types and next_s in shift_types:
                    model.Add(shift[(s, d_curr, prev_s)] + shift[(s, d_next, next_s)] <= 1)

    # 期間内の回数指定（Hard制約）
    # ただし、希望シフトで指定された回数が設定値を上回る場合は、希望シフトの回数を優先（適用）する
    period_counts = st.session_state.get("period_counts", {})
    for s in staffs_local:
        if s in period_counts:
            for t_type, count in period_counts[s].items():
                if t_type in shift_types:
                    # 希望シフトでの指定回数をカウント
                    hope_count = 0
                    if s in hope_df.index:
                        for d in days:
                            if d in hope_df.columns:
                                val = str(hope_df.at[s, d]).strip()
                                if val == t_type:
                                    hope_count += 1
                    
                    # 設定値と希望数の大きい方を採用
                    target_count = max(int(count), hope_count)
                    model.Add(sum(shift[(s, d, t_type)] for d in days) == target_count)

    global_max = int(st.session_state.get("max_consecutive_work", 5))
    for s in staffs_local:
        s_max = int(staff_settings[s].get("max_consecutive_work", 0))
        max_cons = s_max if s_max > 0 else global_max
        window_len = max_cons + 1

        prev_work = int(staff_settings[s].get("prev_consecutive_work", 0))
        if prev_work > 0:
            limit = window_len - prev_work
            if 0 < limit <= len(days):
                model.Add(sum(shift[(s, d, t)] for d in days[:limit] for t in work_shifts) <= limit - 1)

        for i in range(len(days) - max_cons):
            model.Add(sum(shift[(s, d, t)] for d in days[i : i + window_len] for t in work_shifts) <= max_cons)

    weeks = {}
    for d_str in days:
        d_obj = day_map[d_str]
        sunday = d_obj - datetime.timedelta(days=(d_obj.weekday() + 1) % 7)
        weeks.setdefault(sunday, []).append(d_str)

    weekly_holiday_targets = [x["名称"] for x in st.session_state.get("holiday_properties", []) if x.get("週回数固定設定") and x.get("名称") in holiday_types]
    for s in staffs_local:
        for w_days in weeks.values():
            for h in weekly_holiday_targets:
                if staff_settings[s]["holiday_periods"].get(h, "週") != "週":
                    continue
                req_count = int(staff_settings[s]["holiday_counts_week"].get(h, 0))
                actual_sum = sum(shift[(s, d, h)] for d in w_days)

                if len(w_days) == 7:
                    model.Add(sum(shift[(s, d, h)] for d in w_days) == req_count)
                    # 週回数指定をソフト制約に変更（解なしエラーを防ぐため）
                    # 違反した場合は大きなペナルティを与える
                    actual_var = model.NewIntVar(0, 7, f"act_{s}_{h}_{w_days[0]}")
                    model.Add(actual_var == actual_sum)
                    diff_var = model.NewIntVar(-7, 7, f"diff_raw_{s}_{h}_{w_days[0]}")
                    model.Add(diff_var == actual_var - req_count)
                    abs_diff = model.NewIntVar(0, 7, f"abs_diff_{s}_{h}_{w_days[0]}")
                    model.AddAbsEquality(abs_diff, diff_var)
                    obj_terms.append(abs_diff * -1000)
                else:
                    model.Add(sum(shift[(s, d, h)] for d in w_days) <= req_count)
                    # 半端な期間もソフト制約に変更
                    # req_countを超えた分だけペナルティ
                    actual_var = model.NewIntVar(0, 7, f"act_{s}_{h}_{w_days[0]}")
                    model.Add(sum(shift[(s, d, h)] for d in w_days) == actual_var)
                    
                    excess = model.NewIntVar(0, 7, f"excess_{s}_{h}_{w_days[0]}")
                    model.Add(excess >= actual_var - req_count)
                    obj_terms.append(excess * -1000)

    # Monthly holiday count constraints (soft)
    months = {}
    for d_str in days:
        d_obj = day_map[d_str]
        months.setdefault((d_obj.year, d_obj.month), []).append(d_str)

    for s in staffs_local:
        for (y, m), m_days in months.items():
            days_in_month = calendar.monthrange(y, m)[1]
            for h in weekly_holiday_targets:
                if staff_settings[s]["holiday_periods"].get(h, "週") != "月":
                    continue
                req_count = int(staff_settings[s]["holiday_counts_month"].get(h, 0))
                actual_sum = sum(shift[(s, d, h)] for d in m_days)

                # Soft constraint only: allow any count, penalize deviation from target.
                actual_var = model.NewIntVar(0, len(m_days), f"act_m_{s}_{h}_{y}_{m}")
                model.Add(actual_var == actual_sum)
                diff_var = model.NewIntVar(-len(m_days), len(m_days), f"diff_m_{s}_{h}_{y}_{m}")
                model.Add(diff_var == actual_var - req_count)
                abs_diff = model.NewIntVar(0, len(m_days), f"abs_m_{s}_{h}_{y}_{m}")
                model.AddAbsEquality(abs_diff, diff_var)
                obj_terms.append(abs_diff * -500)

    # --- 休日順序ルール (Holiday Order Rules) ---
    # 週単位で「Pre」が「Post」より先（または同時）でなければならない
    # => 「Post」が「Pre」より先にあることを禁止
    # つまり、同じ週内で 日付 d1 < d2 のとき、
    # shift[s, d1, Post] == 1 かつ shift[s, d2, Pre] == 1 は禁止 (sum <= 1)
    holiday_orders = st.session_state.get("holiday_order_rules", [])
    if holiday_orders:
        for s in staffs_local:
            for w_days in weeks.values():
                # w_days は文字列リストだが、順序は保証されている前提 (compute_daysでソート済)
                #念のためインデックスでループ
                n_days = len(w_days)
                if n_days < 2:
                    continue
                
                for rule in holiday_orders:
                    pre = rule.get("pre")
                    post = rule.get("post")
                    
                    if pre not in shift_types or post not in shift_types:
                        continue
                    
                    # 全ての日付ペア (i, j) i < j についてチェック
                    for i in range(n_days):
                        for j in range(i + 1, n_days):
                            d_early = w_days[i]
                            d_late = w_days[j]
                            
                            # 「早い日(i)にPost」かつ「遅い日(j)にPre」を禁止
                            model.Add(shift[(s, d_early, post)] + shift[(s, d_late, pre)] <= 1)

    # --- 祝日・代休ルール ---
    ph_rules = st.session_state.get("public_holiday_rules", {})
    if ph_rules.get("enabled", False) and jpholiday:
        target_emps = ph_rules.get("target_employments", [])
        comp_type = ph_rules.get("comp_holiday_type", "")
        
        # 期間内の祝日を取得
        public_holidays = [d for d in days if jpholiday.is_holiday(day_map[d])]
        
        if comp_type in shift_types and public_holidays:
            # Pre-calculate work var for each day if it is a PH for easier access
            # This is done per staff inside the loop
            pass

            for s in staffs_local:
                # 雇用形態チェック
                s_emp = staff_emp_map.get(s, "")
                if target_emps and s_emp not in target_emps:
                    continue
                
                # 累積変数
                current_work_cum = 0
                current_comp_cum = 0

                for d in days:
                    # 1. 祝日勤務の加算
                    if d in public_holidays:
                        # 全ての勤務シフトについて和をとる (Work Shiftであればカウント)
                        current_work_cum += sum(shift[(s, d, w)] for w in work_shifts)
                    
                    # 2. 代休取得の加算
                    current_comp_cum += shift[(s, d, comp_type)]
                    
                    # 3. 制約: 累積代休数 <= 累積祝日勤務数
                    # これにより「先取り」を禁止し、「後から（または同時）」のみ許可
                    # ※同時はシフト排他制御により不可なので、実質「後から」になる
                    model.Add(current_comp_cum <= current_work_cum)
                
                # 4. 期間終了時に精算完了していること (Total Equality)
                model.Add(current_comp_cum == current_work_cum)

    filler_shift = st.session_state.get("filler_shift_type")
    pref_weights = {"低": -1.0, "中": 0.0, "高": 1.0}
    
    for s in staffs_local:
        for d in days:
            # 0. シフト希望度（なるべく少なめ/多め）
            for ws in work_shifts:
                pref = staff_settings[s]["shift_preferences"].get(ws, "普通")
                w = pref_weights.get(pref, 0.0)
                if w != 0.0:
                    obj_terms.append(shift[(s, d, ws)] * w)

            # 1. 自動補完シフト
            # 制約を満たす限り、できるだけこのシフトで埋めるようにする
            if filler_shift and filler_shift in shift_types:
                obj_terms.append(shift[(s, d, filler_shift)] * 0.1)

            # 2. その他のシフト（不定を防ぐための微小な重み）
            for t in shift_types:
                 if t != filler_shift:
                     obj_terms.append(shift[(s, d, t)] * 0.01)

    model.Maximize(sum(obj_terms) if obj_terms else 0)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(SOLVER_TIMEOUT)

    status_text = st.empty()
    progress_bar = st.progress(0)
    start_time = time.time()

    with ThreadPoolExecutor() as executor:
        future = executor.submit(solver.Solve, model)
        while not future.done():
            elapsed = time.time() - start_time
            progress = min(1.0, elapsed / float(SOLVER_TIMEOUT))
            progress_bar.progress(progress)
            status_text.caption(f"計算中... {elapsed:.0f}s")
            time.sleep(0.1)
        status = future.result()

    status_text.empty()
    progress_bar.empty()

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        data_rows = []
        for s in staffs_local:
            row = []
            for d in days:
                chosen = ""
                for t in shift_types:
                    if solver.Value(shift[(s, d, t)]) == 1:
                        chosen = t
                        break
                row.append(chosen)
            data_rows.append(row)

        # ソフト制約（休日回数）の違反チェック
        for s in staffs_local:
            for w_days in weeks.values():
                if len(w_days) == 7:
                    for h in weekly_holiday_targets:
                        if staff_settings[s]["holiday_periods"].get(h, "週") != "週":
                            continue
                        req = int(staff_settings[s]["holiday_counts_week"].get(h, 0))
                        actual = 0
                        for d in w_days:
                            if solver.Value(shift[(s, d, h)]) == 1:
                                actual += 1
                        if actual != req:
                            debug_messages.append(f"⚠️ {s}さんの {w_days[0]}週: {h}が {actual}日 (設定: {req}日)")

            for (y, m), m_days in months.items():
                days_in_month = calendar.monthrange(y, m)[1]
                if len(m_days) == days_in_month:
                    for h in weekly_holiday_targets:
                        if staff_settings[s]["holiday_periods"].get(h, "週") != "月":
                            continue
                        req = int(staff_settings[s]["holiday_counts_month"].get(h, 0))
                        actual = 0
                        for d in m_days:
                            if solver.Value(shift[(s, d, h)]) == 1:
                                actual += 1
                        if actual != req:
                            debug_messages.append(f"⚠️ {s}さんの {y}年{m}月: {h}が {actual}日 (設定: {req}日)")

        # 必要人数の不足・余剰チェック
        for d in days:
            for ws in target_work_shifts:
                req = int(req_df.at[d, ws]) if (d in req_df.index and ws in req_df.columns) else 0
                if req > 0:
                    actual = 0
                    for s in staffs_local:
                        if solver.Value(shift[(s, d, ws)]) == 1:
                            actual += 1
                    if actual < req:
                        debug_messages.append(f"⚠️ {d} の「{ws}」: {actual}名 (目標: {req}名) - 人手不足")
                    elif actual > req:
                        debug_messages.append(f"ℹ️ {d} の「{ws}」: {actual}名 (目標: {req}名) - 余剰あり")

        out_df = pd.DataFrame(data_rows, index=staffs_local, columns=days)
        out_df.index.name = "スタッフ名"
        return out_df.reset_index(), debug_messages

    if status == cp_model.INFEASIBLE:
        debug_messages.append("・制約条件が厳しく、解が存在しません（NGペアや連勤制限などが原因の可能性があります）。")
        debug_messages.append("🔍 詳細診断を実行中...")
        diag_reasons = diagnose_infeasibility(days, day_map, work_shifts, holiday_types, shift_types)
        if diag_reasons:
            debug_messages.append("以下の条件を緩和（削除・変更）すると解決する可能性があります：")
            debug_messages.extend(diag_reasons)
        else:
            debug_messages.append("・診断を行いましたが、特定の原因を特定できませんでした。")
    elif status == cp_model.UNKNOWN:
        debug_messages.append("・計算時間内に解が見つかりませんでした。")

    return None, debug_messages


def df_to_signature(df: Optional[pd.DataFrame]) -> str:
    if df is None:
        return ""
    try:
        return df.fillna("").to_json(orient="split", date_format="iso")
    except Exception:
        return ""


def compute_input_signature() -> str:
    payload = {
        "staff_df": df_to_signature(st.session_state.get("staff_df")),
        "hope_df": df_to_signature(st.session_state.get("hope_df")),
        "req_df": df_to_signature(st.session_state.get("req_df")),
        "individual_rules_df": df_to_signature(st.session_state.get("individual_rules_df")),
        "global_rules": st.session_state.get("global_rules", []),
        "ng_pairs": st.session_state.get("ng_pairs", []),
        "period_counts": st.session_state.get("period_counts", {}),
        "prohibited_transitions": st.session_state.get("prohibited_transitions", []),
        "holiday_order_rules": st.session_state.get("holiday_order_rules", []),
        "public_holiday_rules": st.session_state.get("public_holiday_rules", {}),
        "req_by_weekday": df_to_signature(st.session_state.get("req_by_weekday")),
        "work_shifts_list": st.session_state.get("work_shifts_list", []),
        "holiday_types_list": st.session_state.get("holiday_types_list", []),
        "work_shift_properties": st.session_state.get("work_shift_properties", []),
        "holiday_properties": st.session_state.get("holiday_properties", []),
        "max_consecutive_work": st.session_state.get("max_consecutive_work", None),
        "filler_shift_type": st.session_state.get("filler_shift_type", None),
        "start_date": str(st.session_state.get("start_date", "")),
        "end_date": str(st.session_state.get("end_date", "")),
        "employment_types_list": st.session_state.get("employment_types_list", []),
    }
    payload_json = json.dumps(payload, sort_keys=True, ensure_ascii=True, default=str)
    return hashlib.sha256(payload_json.encode("utf-8")).hexdigest()


def run_and_store_generation(days, day_map, work_shifts, holiday_types, shift_types, trigger, reason=""):
    result_df, debug_msgs = run_optimization(days, day_map, work_shifts, holiday_types, shift_types)
    st.session_state["last_debug_msgs"] = debug_msgs
    st.session_state["last_run_trigger"] = trigger
    st.session_state["last_run_reason"] = reason
    st.session_state["last_run_ts"] = time.time()
    if trigger == "auto":
        st.session_state["auto_notice_dismissed"] = False
    if result_df is not None:
        st.session_state["last_result"] = result_df
        st.session_state["last_status"] = "ok"
    else:
        st.session_state["last_result"] = None
        st.session_state["last_status"] = "infeasible"
    return result_df, debug_msgs


def maybe_flag_auto_generation():
    sig = compute_input_signature()
    prev_sig = st.session_state.get("auto_gen_input_signature")
    if prev_sig is None:
        st.session_state["auto_gen_input_signature"] = sig
        return
    if sig != prev_sig:
        st.session_state["auto_gen_input_signature"] = sig
        st.session_state["auto_gen_needed"] = True
        st.session_state["auto_gen_reason"] = "設定変更を検知しました"
        st.session_state["auto_notice_page"] = st.session_state.get("page", "home")


def mark_auto_gen_needed(reason: str):
    st.session_state["auto_gen_needed"] = True
    st.session_state["auto_gen_reason"] = reason
    st.session_state["auto_notice_page"] = st.session_state.get("page", "home")


def maybe_run_auto_generation():
    if not st.session_state.get("auto_gen_needed"):
        return

    st.session_state["auto_gen_needed"] = False
    reason = st.session_state.get("auto_gen_reason", "設定変更を検知しました")
    days = st.session_state.get("days_list", [])
    day_map = st.session_state.get("day_map", {})
    work_shifts = st.session_state.get("work_shifts_list", [])
    holiday_types = st.session_state.get("holiday_types_list", [])
    shift_types = holiday_types + work_shifts
    staff_df = st.session_state.get("staff_df", pd.DataFrame())

    if not days or not day_map or not shift_types:
        st.info("自動生成をスキップしました（期間またはシフトが未設定です）。")
        st.session_state["last_status"] = "skipped"
        return

    if staff_df.empty:
        st.info("自動生成をスキップしました（スタッフが未登録です）。")
        st.session_state["last_status"] = "skipped"
        return

    with st.container(border=True):
        st.markdown('<div class="card-title">🔁 自動生成</div>', unsafe_allow_html=True)
        st.caption(f"変更検知: {reason}")
        result_df, debug_msgs = run_and_store_generation(
            days, day_map, work_shifts, holiday_types, shift_types, trigger="auto", reason=reason
        )
        if result_df is not None:
            st.success("自動生成が完了しました。")
            if debug_msgs:
                with st.expander("⚠️ 結果に関するお知らせ（不足・余剰など）", expanded=False):
                    for msg in debug_msgs:
                        st.write(msg)
        else:
            st.error("解が見つかりませんでした。条件を緩和してください。")
            if debug_msgs:
                with st.expander("詳細な理由（可能性）", expanded=True):
                    for msg in debug_msgs:
                        st.write(msg)


# ----------------------------
# UI Components
# ----------------------------
def render_navbar():
    cols = st.columns(5)
    nav_items = [
        ("🏠", "ホーム", "home"),
        ("👥", "スタッフ", "staff"),
        ("📅", "要員配置", "req"),
        ("🛠️", "作成", "gen"),
        ("💾", "保存・読込", "save_load"),
    ]
    for i, (icon, label, page_key) in enumerate(nav_items):
        with cols[i]:
            if st.button(f"{icon}\n{label}", key=f"nav_{page_key}", use_container_width=True):
                st.session_state["page"] = page_key
                st.rerun()


def render_login():
    st.markdown("<br><br>", unsafe_allow_html=True)
    with st.container(border=True):
        st.title("シフト自動生成アプリ")
        st.write("ユーザー名を入力して開始")
        user = st.text_input("ユーザーID", key="login_user")
        if st.button("ログイン", type="primary", use_container_width=True, key="login_btn"):
            if user.strip():
                st.session_state["current_user"] = user.strip()
                st.session_state["data_loaded"] = False
                st.session_state["page"] = "home"
                st.rerun()


# ----------------------------
# Pages
# ----------------------------
def page_save_load():
    st.header("設定の保存・読み込み")

    # --- Save Section ---
    with st.container(border=True):
        st.markdown('<div class="card-title">💾 名前をつけて保存</div>', unsafe_allow_html=True)
        st.caption("現在の設定状態を、名前を指定して保存します。")
        
        c_input, c_btn = st.columns([3, 1])
        default_name = f"backup_{datetime.date.today().strftime('%Y%m%d')}"
        save_name = c_input.text_input("保存名 (拡張子不要)", value=default_name, key="sl_save_name")
        
        if c_btn.button("保存", key="sl_save_btn", use_container_width=True):
            if save_name.strip():
                fname = save_name.strip()
                if not fname.endswith(".json"):
                    fname += ".json"
                path = os.path.join(USER_DATA_DIR, fname)
                try:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(create_save_json())
                    st.success(f"「{fname}」として保存しました。")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"保存失敗: {e}")
            else:
                st.error("保存名を入力してください。")

    # --- Load Section ---
    with st.container(border=True):
        st.markdown('<div class="card-title">📂 読み込み</div>', unsafe_allow_html=True)
        st.caption("保存済みの設定データを読み込みます。")

        # List JSON files
        files = [f for f in os.listdir(USER_DATA_DIR) if f.endswith(".json")]
        files.sort(reverse=True) # Newest first usually (by name at least)

        if not files:
            st.info("保存されたデータがありません。")
        else:
            c_sel, c_load, c_del = st.columns([3, 1, 1])
            selected_file = c_sel.selectbox("ファイル選択", files, key="sl_load_sel", label_visibility="collapsed")
            
            if c_load.button("読み込み", key="sl_load_btn", use_container_width=True):
                path = os.path.join(USER_DATA_DIR, selected_file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    load_state_from_dict(data)
                    st.success(f"「{selected_file}」を読み込みました。")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"読み込み失敗: {e}")

            if c_del.button("削除", key="sl_del_btn", type="primary", use_container_width=True):
                path = os.path.join(USER_DATA_DIR, selected_file)
                try:
                    os.remove(path)
                    st.success(f"「{selected_file}」を削除しました。")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"削除失敗: {e}")


def page_home():
    st.header("設定")



    with st.container(border=True):
        st.markdown('<div class="card-title"> 期間</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        st.session_state["start_date"] = c1.date_input(
            "開始",
            st.session_state.get("start_date", datetime.date(2026, 1, 1)),
            key="home_start",
            format="YYYY/MM/DD",
        )
        st.session_state["end_date"] = c2.date_input(
            "終了",
            st.session_state.get("end_date", datetime.date(2026, 1, 31)),
            key="home_end",
            format="YYYY/MM/DD",
        )
        if st.session_state["end_date"] < st.session_state["start_date"]:
            st.error("終了日は開始日以降にしてください。")

    # --- Import Previous Shift Data (Moved from Staff Page) ---
    with st.expander("📂 前回のシフト結果から連勤数を反映", expanded=False):
        st.info(
            """
            **以前のシフトデータを引き継ぐ機能です**
            
            設定した「開始日」より**前の日付**のデータを読み込んだデータから探し出し、そこから遡って連勤数を自動計算します。
            
            1. 以前の期間を含む保存データを選択します。
            2. 基準となる日付と、計算された結果（プレビュー）を確認します。
            3. 「反映を実行」ボタンを押してください。
            """
        )

        target_df = None
        
        # Select from user_data
        json_files = [f for f in os.listdir(USER_DATA_DIR) if f.endswith(".json")]
        json_files.sort()
        
        if json_files:
            sel_file = st.selectbox("保存済みデータを選択", json_files, key="prev_shift_local_sel_home")
            if sel_file:
                path = os.path.join(USER_DATA_DIR, sel_file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if "確定シフト結果" in data:
                        target_df = read_df_from_json(data["確定シフト結果"])
                    else:
                        st.warning("このファイルには「確定シフト結果」が含まれていません。")
                except Exception as e:
                    st.error(f"読み込みエラー: {e}")
        else:
            st.info("保存済みデータがありません。")

        if target_df is not None:
            try:
                # Find staff column
                staff_col = None
                possible_names = ["スタッフ名", "Name", "Staff", "名前"]
                for c in possible_names:
                    if c in target_df.columns:
                        staff_col = c
                        break
                
                if not staff_col:
                    # Fallback: assume first column
                    staff_col = target_df.columns[0]
                
                if staff_col:
                    current_staff_df = st.session_state["staff_df"].copy()
                    work_shifts = set(st.session_state.get("work_shifts_list", []))

                    # --- Determine Cutoff Date (Search backwards) ---
                    start_d = st.session_state.get("start_date", datetime.date.today())
                    
                    # Identify date columns
                    date_cols = [c for c in target_df.columns if c != staff_col]
                    
                    found_cutoff_str = None
                    cutoff_date_obj = None
                    
                    # Search backwards from yesterday up to 60 days
                    for i in range(1, 61):
                        target_d = start_d - datetime.timedelta(days=i)
                        w_label = WEEKDAYS_JP[target_d.weekday()]
                        d_str = f"{target_d.month}/{target_d.day}({w_label})"
                        
                        if d_str in date_cols:
                            found_cutoff_str = d_str
                            cutoff_date_obj = target_d
                            break
                    
                    use_cols = []
                    cutoff_msg = ""
                    
                    if found_cutoff_str:
                        # Found a valid date before start_date
                        cut_idx = date_cols.index(found_cutoff_str)
                        use_cols = date_cols[:cut_idx+1]
                        
                        # Gap check
                        days_diff = (start_d - cutoff_date_obj).days
                        if days_diff == 1:
                            cutoff_msg = f"前日「{found_cutoff_str}」を基準に計算します。（連続しています）"
                        else:
                            cutoff_msg = f"直近のデータ「{found_cutoff_str}」を基準に計算します。（{days_diff-1}日間の空白期間があります）"
                    else:
                        # Fallback to end of file if no date matches (format mismatch or too far)
                        use_cols = date_cols
                        last_col = date_cols[-1] if date_cols else "なし"
                        cutoff_msg = f"開始日以前の日付が見つかりませんでした。データの末尾「{last_col}」を基準に計算します。"
                    
                    st.info(cutoff_msg)

                    # Preview Data
                    updates = {}
                    
                    for idx, row in current_staff_df.iterrows():
                        s_name = str(row.get("スタッフ名", "")).strip()
                        if not s_name: continue

                        # Find in target_df
                        prev_row = target_df[target_df[staff_col].astype(str).str.strip() == s_name]
                        if not prev_row.empty:
                            # Use only the relevant columns
                            vals = prev_row.iloc[0][use_cols].values
                            
                            cons_work = 0
                            # Iterate backwards
                            for val in vals[::-1]:
                                val_str = str(val).strip()
                                if val_str in work_shifts:
                                    cons_work += 1
                                else:
                                    break
                            
                            updates[idx] = cons_work
                    
                    if updates:
                        st.info(f"{len(updates)}名のデータが見つかりました。")
                        # Preview Table
                        preview_data = []
                        for idx, val in updates.items():
                            name = current_staff_df.at[idx, "スタッフ名"]
                            old_val = current_staff_df.at[idx, "シフト開始前の連勤数"]
                            preview_data.append({"スタッフ名": name, "現在の設定": old_val, "読み込み値": val})
                        
                        st.dataframe(pd.DataFrame(preview_data), use_container_width=True, height=200)

                        if st.button("反映を実行", key="apply_prev_data_home", type="primary"):
                            for idx, val in updates.items():
                                current_staff_df.at[idx, "シフト開始前の連勤数"] = val
                            st.session_state["staff_df"] = current_staff_df
                            st.success("連勤データを更新しました！")
                            time.sleep(1)
                            st.rerun()
                    else:
                        st.warning("現在のスタッフ名と一致するデータが見つかりませんでした。")
                else:
                    st.error("スタッフ名の列を特定できませんでした。")
            except Exception as e:
                st.error(f"データ処理エラー: {e}")

    with st.container(border=True):
        st.markdown('<div class="card-title" id="card-title-emp">💼 雇用形態の種類</div>', unsafe_allow_html=True)
        emp_list = st.session_state.get("employment_types_list", ["正社員", "パート", "アルバイト"])
        st.caption("雇用形態の種類")
        c_add_e, c_btn_e = st.columns([3, 1])
        new_emp = c_add_e.text_input("雇用形態追加", placeholder="例: 正社員", key="add_emp_input", label_visibility="collapsed")
        if c_btn_e.button("追加", key="add_emp_btn", use_container_width=True):
            if new_emp and new_emp not in emp_list:
                emp_list.append(new_emp)
                st.session_state["employment_types_list"] = emp_list
                st.rerun()

        if emp_list:
            st.markdown('<span id="emp-marker"></span>', unsafe_allow_html=True)
            st.markdown('<div id="emp-tags">', unsafe_allow_html=True)
            edited_emp = st.multiselect(
                "登録済み雇用形態 (×で削除)",
                options=emp_list,
                default=emp_list,
                key="emp_multiselect_editor"
            )
            st.markdown('</div>', unsafe_allow_html=True)
            if len(edited_emp) < len(emp_list):
                st.session_state["employment_types_list"] = edited_emp
                st.rerun()

    with st.container(border=True):
        st.markdown('<div class="card-title" id="card-title-ws">🏷️ 担務の種類</div>', unsafe_allow_html=True)
        ws_list = st.session_state.get("work_shifts_list", ["日勤", "夜勤"])
        st.caption("担務の種類")
        c_add, c_btn = st.columns([3, 1])
        new_ws = c_add.text_input("担務追加", placeholder="例: 日勤", key="add_ws_input", label_visibility="collapsed")
        if c_btn.button("追加", key="add_ws_btn", use_container_width=True):
            if new_ws and new_ws not in ws_list:
                ws_list.append(new_ws)
                st.session_state["work_shifts_list"] = ws_list
                sync_staff_df_schema()
                st.rerun()

        if ws_list:
            st.markdown('<span id="ws-marker"></span>', unsafe_allow_html=True)
            st.markdown('<div id="ws-tags">', unsafe_allow_html=True)
            edited_ws = st.multiselect(
                "登録済み担務 (×で削除)",
                options=ws_list,
                default=ws_list,
                key="ws_multiselect_editor"
            )
            st.markdown('</div>', unsafe_allow_html=True)
            if len(edited_ws) < len(ws_list):
                st.session_state["work_shifts_list"] = edited_ws
                sync_staff_df_schema()
                st.rerun()
            
            # 勤務シフトの詳細設定（必要人数対象かどうか）
            st.markdown('<div style="margin-top:12px;"></div>', unsafe_allow_html=True)
            with st.expander("要員配置対象外担務設定", expanded=False):
                st.info(
                    """
                    **要員配置に入れない担務を選びます。**
                    
                    例：「研修」「補助」など、必要な要員配置としない担務だけオンにしてください。
                    """
                )
                ws_props = st.session_state.get("work_shift_properties", [])
                ws_prop_map = {p["名称"]: p for p in ws_props}
                updated_ws_props = []
                ws_props_changed = False

                for ws_name in ws_list:
                    p = ws_prop_map.get(ws_name, {"名称": ws_name, "必要人数対象": True})
                    
                    # UI: トグルで「除外する」かどうかを選択（内部値 True=対象, False=対象外）
                    is_excluded = st.toggle(
                        f"**{ws_name}** を要員配置対象外",
                        value=not p.get("必要人数対象", True),
                        key=f"toggle_ws_prop_{ws_name}"
                    )
                    
                    if is_excluded == p.get("必要人数対象", True):
                        p["必要人数対象"] = not is_excluded
                        ws_props_changed = True
                    updated_ws_props.append(p)
                
                if ws_props_changed:
                    st.session_state["work_shift_properties"] = updated_ws_props
                    st.rerun()

    with st.container(border=True):
        st.markdown('<div class="card-title" id="card-title-hol">⛱️ 休日の種類</div>', unsafe_allow_html=True)
        hol_list = st.session_state.get("holiday_types_list", ["週休", "非番", "有給"])
        st.caption("休日の種類")
        c_add_h, c_btn_h = st.columns([3, 1])
        new_hol = c_add_h.text_input("休日追加", placeholder="例: 週休", key="add_hol_input", label_visibility="collapsed")
        if c_btn_h.button("追加", key="add_hol_btn", use_container_width=True):
            if new_hol and new_hol not in hol_list:
                hol_list.append(new_hol)
                props = st.session_state.get("holiday_properties", [])
                props.append({"名称": new_hol, "週回数固定設定": False})
                st.session_state["holiday_properties"] = props
                st.session_state["holiday_types_list"] = hol_list
                sync_staff_df_schema()
                st.rerun()

        if hol_list:
            st.markdown('<span id="hol-marker"></span>', unsafe_allow_html=True)
            st.markdown('<div id="hol-tags">', unsafe_allow_html=True)
            edited_hol = st.multiselect(
                "登録済み休日 (×で削除)",
                options=hol_list,
                default=hol_list,
                key="hol_multiselect_editor"
            )
            st.markdown('</div>', unsafe_allow_html=True)
            if len(edited_hol) < len(hol_list):
                st.session_state["holiday_types_list"] = edited_hol
                props = st.session_state.get("holiday_properties", [])
                removed_items = set(hol_list) - set(edited_hol)
                st.session_state["holiday_properties"] = [p for p in props if p.get("名称") not in removed_items]
                sync_staff_df_schema()
                st.rerun()

            # 各休日の詳細設定（週回数固定設定など）
            st.markdown('<div style="margin-top:12px;"></div>', unsafe_allow_html=True)
            
            with st.expander("詳細設定：休日の日数設定", expanded=False):
                st.info(
                    """
                    休日の「月・週の日数」を設定するかを決めます。
                    
                    オンにすると、スタッフごとに「月・週に何日この休日を取得するか」を設定できます（例：週休は週に1日取得など）。
                    """
                )
                props = st.session_state.get("holiday_properties", [])
                prop_map = {p["名称"]: p for p in props}
                updated_props = []
                props_changed = False

                for h_name in hol_list:
                    p = prop_map.get(h_name, {"名称": h_name, "週回数固定設定": False})
                    
                    is_fixed = st.toggle(
                        f"**{h_name}** を月・週で何日取得するか設定",
                        value=p.get("週回数固定設定", False),
                        key=f"toggle_hol_prop_{h_name}"
                    )
                    
                    if is_fixed != p.get("週回数固定設定", False):
                        p["週回数固定設定"] = is_fixed
                        props_changed = True
                    updated_props.append(p)
                
                if props_changed:
                    st.session_state["holiday_properties"] = updated_props
                    sync_staff_df_schema()
                    st.rerun()



            # ---------------------------------------------------------
            # 休日の詳細設定（曜日・日付） - Moved here
            # ---------------------------------------------------------
            st.markdown('<div style="margin-top:12px;"></div>', unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown('<div class="card-title" id="card-title-hol-detail">⛱️ 休日の詳細設定（曜日・日付）</div>', unsafe_allow_html=True)
                st.caption("例：日曜日に休日となる場合は週休とする")

                gr_list = st.session_state.get("global_rules", [])
                
                tab_dow, tab_date = st.tabs(["曜日で指定", "日付で指定"])
                
                # Only holidays allowed
                target_shifts = st.session_state.get("holiday_types_list", [])
                # Employment types + All
                emp_types_opts = ["指定なし(全員)"] + st.session_state.get("employment_types_list", [])
                
                with tab_dow:
                    c_d, c_s, c_e, c_b = st.columns([1, 1.5, 1.5, 0.8])
                    sel_dow = c_d.selectbox("曜日", WEEKDAYS_JP, key="gr_dow_sel")
                    sel_shift_dow = c_s.selectbox("適用する休日", target_shifts, key="gr_dow_shift_sel")
                    sel_emp_dow = c_e.selectbox("対象の雇用形態", emp_types_opts, key="gr_dow_emp_sel")
                    
                    with c_b:
                        st.markdown('<div style="height: 28px;"></div>', unsafe_allow_html=True)
                        if st.button("追加", key="gr_dow_add", use_container_width=True):
                            emp_val = sel_emp_dow if sel_emp_dow != "指定なし(全員)" else None
                            new_rule = {
                                "type": "dow",
                                "value": sel_dow, 
                                "shift": sel_shift_dow, 
                                "action": "休日ならこれのみ",
                                "employment_type": emp_val
                            }
                            if new_rule not in gr_list:
                                gr_list.append(new_rule)
                                st.session_state["global_rules"] = gr_list
                                st.rerun()

                with tab_date:
                    days_opts = st.session_state.get("days_list", [])
                    if not days_opts:
                        st.info("期間が設定されていません")
                    else:
                        c_dt, c_s2, c_e2, c_b2 = st.columns([1.5, 1.5, 1.5, 0.8])
                        sel_date = c_dt.selectbox("日付", days_opts, key="gr_date_sel")
                        sel_shift_date = c_s2.selectbox("適用する休日", target_shifts, key="gr_date_shift_sel")
                        sel_emp_date = c_e2.selectbox("対象の雇用形態", emp_types_opts, key="gr_date_emp_sel")
                        
                        with c_b2:
                            st.markdown('<div style="height: 28px;"></div>', unsafe_allow_html=True)
                            if st.button("追加", key="gr_date_add", use_container_width=True):
                                emp_val = sel_emp_date if sel_emp_date != "指定なし(全員)" else None
                                new_rule = {
                                    "type": "date", 
                                    "value": sel_date, 
                                    "shift": sel_shift_date, 
                                    "action": "休日ならこれのみ",
                                    "employment_type": emp_val
                                }
                                if new_rule not in gr_list:
                                    gr_list.append(new_rule)
                                    st.session_state["global_rules"] = gr_list
                                    st.rerun()

                if gr_list:
                    st.divider()
                    st.markdown('<span id="global-rule-marker"></span>', unsafe_allow_html=True)
                    
                    # Formatter
                    def format_gr(r):
                        kind = "曜日" if r["type"] == "dow" else "日付"
                        emp_str = f" ({r.get('employment_type')})" if r.get('employment_type') else ""
                        return f"【{kind}】{r['value']}{emp_str} が休みなら → {r['shift']}"
                    
                    gr_labels = [format_gr(r) for r in gr_list]
                    
                    st.markdown('<div id="gr-tags">', unsafe_allow_html=True)
                    remained = st.multiselect(
                        "登録済みルール",
                        options=gr_labels,
                        default=gr_labels,
                        key="gr_multiselect",
                        label_visibility="collapsed"
                    )
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    if len(remained) < len(gr_labels):
                        new_list = []
                        for r in gr_list:
                            if format_gr(r) in remained:
                                new_list.append(r)
                        st.session_state["global_rules"] = new_list
                        st.rerun()

            # 祝日・代休設定
            st.markdown('<div style="margin-top:12px;"></div>', unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown('<div class="card-title" id="card-title-hol-public">🎌 祝日・代休設定</div>', unsafe_allow_html=True)
                st.caption("祝日に勤務した場合に、その日以降に代休を必須とする設定です。")
                
                ph_rules = st.session_state.get("public_holiday_rules", {
                    "enabled": False, "target_employments": [], "comp_holiday_type": ""
                })
                
                c_tog, c_dummy = st.columns([1, 1])
                is_enabled = c_tog.toggle("この機能を有効にする", value=ph_rules.get("enabled", False), key="ph_rules_toggle")
                
                if is_enabled != ph_rules.get("enabled", False):
                    ph_rules["enabled"] = is_enabled
                    st.session_state["public_holiday_rules"] = ph_rules
                    st.rerun()
                    
                if is_enabled:
                    emp_list = st.session_state.get("employment_types_list", [])
                    hol_list = st.session_state.get("holiday_types_list", [])
                    
                    target_emps = st.multiselect(
                        "対象の雇用形態（指定した雇用形態のスタッフのみ適用）",
                        options=emp_list,
                        default=ph_rules.get("target_employments", []),
                        key="ph_rules_emps"
                    )
                    
                    current_comp = ph_rules.get("comp_holiday_type", "")
                    if current_comp not in hol_list:
                        current_comp = "代休" if "代休" in hol_list else (hol_list[0] if hol_list else "")
                    
                    comp_type = st.selectbox(
                        "代休として割り当てる休日",
                        options=hol_list,
                        index=hol_list.index(current_comp) if current_comp in hol_list else 0,
                        key="ph_rules_comp_type"
                    )
                    
                    if target_emps != ph_rules.get("target_employments", []) or comp_type != ph_rules.get("comp_holiday_type", ""):
                        ph_rules["target_employments"] = target_emps
                        ph_rules["comp_holiday_type"] = comp_type
                        st.session_state["public_holiday_rules"] = ph_rules

            # 充填用シフトの設定
            st.markdown('<div style="margin-top:12px;"></div>', unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown('<div class="card-title">💤 自動補完シフト</div>', unsafe_allow_html=True)
                st.caption("全ての条件を満たした上で、「空き」になっている箇所を埋めるシフトを指定します。")
                
                # デフォルト値の決定
                current_filler = st.session_state.get("filler_shift_type")
                if current_filler not in hol_list and hol_list:
                    current_filler = hol_list[-1]
                
                new_filler = st.selectbox(
                    "充填用シフトを選択",
                    options=hol_list,
                    index=hol_list.index(current_filler) if current_filler in hol_list else 0,
                    key="filler_shift_sel"
                )
                
                if new_filler != st.session_state.get("filler_shift_type"):
                    st.session_state["filler_shift_type"] = new_filler
                    # 即時rerunは不要（selectboxの値が変わればsession_stateも変わるため）

    with st.container(border=True):
        st.markdown('<div class="card-title">⚖️ 基本ルール</div>', unsafe_allow_html=True)
        st.caption("スタッフ全員に適用される上限です（スタッフ詳細で個別設定も可能）。")
        cur_max = int(st.session_state.get("max_consecutive_work", 5))
        new_max = counter_input("最大連勤数", cur_max, key="home_max_cons_cnt")
        if new_max != cur_max:
            st.session_state["max_consecutive_work"] = new_max
            st.rerun()

    with st.container(border=True):
        st.markdown('<div class="card-title" id="card-title-ng">🚫 禁止するシフトの並び</div>', unsafe_allow_html=True)
        st.caption("禁止するシフトの並び（例：夜勤→日勤）")
        
        all_types = st.session_state.get("work_shifts_list", []) + st.session_state.get("holiday_types_list", [])
        c_prev, c_arrow, c_next, c_add = st.columns([2, 0.5, 2, 1])
        with c_prev:
            p_prev = st.selectbox("前日", all_types, key="trans_prev")
        with c_arrow:
            st.markdown("<div style='text-align:center; line-height:44px; color:#5F6368;'>→</div>", unsafe_allow_html=True)
        with c_next:
            p_next = st.selectbox("翌日", all_types, key="trans_next")
        with c_add:
            st.markdown('<div style="height: 28px;"></div>', unsafe_allow_html=True)
            if st.button("追加", key="add_trans_btn", use_container_width=True):
                current_trans = st.session_state.get("prohibited_transitions", [])
                new_entry = {"prev": p_prev, "next": p_next}
                if new_entry not in current_trans:
                    current_trans.append(new_entry)
                    st.session_state["prohibited_transitions"] = current_trans
                    st.rerun()

        current_trans = st.session_state.get("prohibited_transitions", [])
        if current_trans:
            st.markdown('<span id="trans-marker"></span>', unsafe_allow_html=True)
            trans_labels = [f"{t['prev']} → {t['next']}" for t in current_trans]
            st.markdown('<div id="trans-tags">', unsafe_allow_html=True)
            remained = st.multiselect(
                "登録済み禁止パターン",
                options=trans_labels,
                default=trans_labels,
                key="trans_multiselect",
                label_visibility="collapsed"
            )
            st.markdown('</div>', unsafe_allow_html=True)
            if len(remained) < len(trans_labels):
                new_list = []
                for t in current_trans:
                    if f"{t['prev']} → {t['next']}" in remained:
                        new_list.append(t)
                st.session_state["prohibited_transitions"] = new_list
                st.rerun()

    with st.container(border=True):
        st.markdown('<div class="card-title" id="card-title-hol-priority">🔢 休日の優先順位（週単位）</div>', unsafe_allow_html=True)
        st.caption("同じ週に両方の休日がある場合、どちらを先の曜日にするかを指定します。")
        
        hol_types = st.session_state.get("holiday_types_list", [])
        
        c_p, c_arr, c_f, c_a = st.columns([2, 0.5, 2, 1])
        with c_p:
            h_pre = st.selectbox("先（早い曜日）", hol_types, key="order_pre")
        with c_arr:
            st.markdown("<div style='text-align:center; line-height:44px; color:#5F6368;'>＜</div>", unsafe_allow_html=True)
        with c_f:
            h_post = st.selectbox("後（遅い曜日）", hol_types, key="order_post")
        with c_a:
            st.markdown('<div style="height: 28px;"></div>', unsafe_allow_html=True)
            if st.button("追加", key="add_order_btn", use_container_width=True):
                if h_pre != h_post:
                    current_orders = st.session_state.get("holiday_order_rules", [])
                    new_order = {"pre": h_pre, "post": h_post}
                    if new_order not in current_orders:
                        current_orders.append(new_order)
                        st.session_state["holiday_order_rules"] = current_orders
                        st.rerun()
                    else:
                        st.warning("既に追加されています。")
                else:
                    st.error("異なる休日を選択してください。")

        current_orders = st.session_state.get("holiday_order_rules", [])
        if current_orders:
            st.markdown('<span id="order-marker"></span>', unsafe_allow_html=True)
            order_labels = [f"{o['pre']} (先) ＜ {o['post']} (後)" for o in current_orders]
            st.markdown('<div id="order-tags">', unsafe_allow_html=True)
            remained_orders = st.multiselect(
                "登録済み順序ルール",
                options=order_labels,
                default=order_labels,
                key="order_multiselect",
                label_visibility="collapsed"
            )
            st.markdown('</div>', unsafe_allow_html=True)
            if len(remained_orders) < len(order_labels):
                new_list = []
                for o in current_orders:
                    if f"{o['pre']} (先) ＜ {o['post']} (後)" in remained_orders:
                        new_list.append(o)
                st.session_state["holiday_order_rules"] = new_list
                st.rerun()


def page_staff():
    st.header("スタッフ一覧")
    
    # CSS for staff registration tags
    st.markdown(
        """
        <style>
        div[data-testid="stMarkdown"]:has(#staff-add-ws-marker) { display: none !important; }
        div:has(#staff-add-ws-marker) + div span[data-baseweb="tag"] {
            background-color: rgba(26,115,232,.10) !important;
            border: 1px solid rgba(26,115,232,.20) !important;
        }
        div:has(#staff-add-ws-marker) + div span[data-baseweb="tag"] span {
            color: #1A73E8 !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    with st.expander("➕ スタッフ登録", expanded=False):
        c_name, c_emp, c_max, c_prev = st.columns([2, 1.5, 1, 1])
        new_name = c_name.text_input("名前", placeholder="スタッフ名", key="staff_add_name")
        emp_opts = st.session_state.get("employment_types_list", ["正社員", "パート", "アルバイト"])
        new_emp = c_emp.selectbox("雇用形態", emp_opts, key="staff_add_emp")
        new_max = c_max.number_input("最大連勤数", min_value=0, value=0, key="staff_add_max")
        new_prev = c_prev.number_input("シフト開始前の連勤数", min_value=0, value=0, key="staff_add_prev")

        # Work Shifts Selection
        st.caption("可能なシフト:")
        ws_list = st.session_state.get("work_shifts_list", [])
        # Filter only target work shifts if needed, but usually we want all defined shifts
        ws_props = {p["名称"]: p for p in st.session_state.get("work_shift_properties", [])}
        target_ws_list = [ws for ws in ws_list if ws_props.get(ws, {}).get("必要人数対象", True)]
        
        st.markdown('<span id="staff-add-ws-marker"></span>', unsafe_allow_html=True)
        selected_ws = st.multiselect(
            "担当可能なシフトを選択",
            options=target_ws_list,
            default=[],
            key="staff_add_ws_select",
            label_visibility="collapsed"
        )

        # Optional: Monthly/weekly holiday settings if enabled
        hol_props = st.session_state.get("holiday_properties", [])
        target_hols = [p for p in hol_props if p.get("週回数固定設定")]
        
        hol_settings = {}
        if target_hols:
            st.caption("月・週の休日日数設定:")
            for p in target_hols:
                h_name = p["名称"]
                period_col = f"{h_name}日数対象"
                c_sel, c_val = st.columns([1, 2])
                period = c_sel.selectbox(
                    f"{h_name}の対象",
                    ["週", "月"],
                    key=f"staff_add_hol_period_{h_name}",
                )
                if period == "週":
                    week_val = counter_input(
                        f"週の「{h_name}」日数",
                        1,
                        key=f"staff_add_hol_week_{h_name}",
                        label_size="1.1rem",
                        max_value=7,
                    )
                    hol_settings[h_name] = {"week": week_val, "month": 4}
                else:
                    month_val = counter_input(
                        f"月の「{h_name}」日数",
                        4,
                        key=f"staff_add_hol_month_{h_name}",
                        label_size="1.1rem",
                        max_value=31,
                    )
                    hol_settings[h_name] = {"week": 1, "month": month_val}

        if st.button("登録", type="primary", use_container_width=True, key="staff_add_btn"):
            if new_name.strip():
                df = st.session_state["staff_df"]
                if "スタッフ名" not in df.columns:
                    df["スタッフ名"] = ""
                if new_name not in df["スタッフ名"].astype(str).values:
                    new_row = {
                        "スタッフ名": new_name.strip(),
                        "雇用形態": new_emp,
                        "最大連勤数": new_max,
                        "シフト開始前の連勤数": new_prev
                    }
                    
                    # Set selected work shifts to True, others to False
                    for ws in ws_list:
                        new_row[ws] = (ws in selected_ws)
                        new_row[f"{ws}希望度"] = "中"
                    
                    # Holiday counts
                    for h in target_hols:
                        h_name = h["名称"]
                        period_col = f"{h_name}日数対象"
                        new_row[f"週の{h_name}日数"] = hol_settings.get(h_name, {}).get("week", 1)
                        new_row[f"月の{h_name}日数"] = hol_settings.get(h_name, {}).get("month", 4)
                        new_row[period_col] = st.session_state.get(f"staff_add_hol_period_{h_name}", "週")

                    st.session_state["staff_df"] = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    st.rerun()
                else:
                    st.error("その名前は既に存在します。")

    df = st.session_state["staff_df"]
    if df.empty:
        st.info("スタッフがいません")
        return

    # デザイン用カラー（薄い紫、薄いピンク、薄い水色）
    row_colors = ["#E1BEE7", "#F8BBD0", "#B3E5FC"]

    # Reordering with arrows
    st.markdown('<div class="card-title">🔄 並び替え</div>', unsafe_allow_html=True)
    st.caption("矢印ボタンで表示順を変更できます。")

    def swap_staff(idx1, idx2):
        df_swap = st.session_state["staff_df"].copy()
        # swap by index permutation
        indices = list(range(len(df_swap)))
        indices[idx1], indices[idx2] = indices[idx2], indices[idx1]
        st.session_state["staff_df"] = df_swap.iloc[indices].reset_index(drop=True)
        st.rerun()

    for i, (_, row) in enumerate(df.iterrows()):
        name = str(row.get("スタッフ名", "")).strip()
        if not name:
            continue

        color = row_colors[i % 3]

        c_up, c_down, c_card, c_btn_edit, c_btn_del = st.columns([0.6, 0.6, 5, 1.25, 1.25])
        
        with c_up:
            if i > 0:
                if st.button("↑", key=f"up_{i}", use_container_width=True):
                    swap_staff(i, i - 1)
            else:
                st.button("↑", key=f"up_{i}_dis", disabled=True, use_container_width=True)

        with c_down:
            if i < len(df) - 1:
                if st.button("↓", key=f"down_{i}", use_container_width=True):
                    swap_staff(i, i + 1)
            else:
                st.button("↓", key=f"down_{i}_dis", disabled=True, use_container_width=True)

        with c_card:
            st.markdown('<span class="staff-row-marker"></span>', unsafe_allow_html=True)
            st.markdown(
                f"""
                <div class="staff-card" style="
                    background-color: #FFFFFF;
                    border: 1px solid #E0E3E7;
                    border-left: 10px solid {color};
                    border-radius: 12px;
                    padding: 0 20px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    display: flex;
                    align-items: center;
                    min-height: 72px;
                ">
                    <span style="
                        font-size: 24px;
                        font-weight: 800;
                        color: #424242;
                    ">{name}</span>
                    <span style="
                        font-size: 14px;
                        font-weight: normal;
                        color: #5F6368;
                        margin-left: 12px;
                        background: #F1F3F4;
                        padding: 2px 8px;
                        border-radius: 4px;
                    ">{row.get('雇用形態', '')}</span>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        with c_btn_edit:
            if st.button("設定", key=f"edit_{name}_{i}", use_container_width=True):
                st.session_state["editing_staff"] = name
                st.session_state["page"] = "staff_detail"
                st.rerun()

        with c_btn_del:
            if st.button("削除", key=f"del_{name}_{i}", type="primary", use_container_width=True):
                new_df = df.drop(index=i).reset_index(drop=True)
                st.session_state["staff_df"] = new_df
                st.rerun()


def page_staff_detail():
    target = st.session_state.get("editing_staff")
    if not target:
        st.session_state["page"] = "staff"
        st.rerun()

    df_nav = st.session_state.get("staff_df", pd.DataFrame())
    staff_list = df_nav["スタッフ名"].astype(str).tolist() if "スタッフ名" in df_nav.columns else []
    try:
        curr_idx = staff_list.index(target)
    except ValueError:
        curr_idx = -1
    prev_staff = staff_list[curr_idx - 1] if (curr_idx > 0) else None
    next_staff = staff_list[curr_idx + 1] if (curr_idx != -1 and curr_idx < len(staff_list) - 1) else None

    c_back, c_prev, c_next = st.columns([1, 1, 1])
    if c_back.button("🔙 戻る", key="back_to_staff", use_container_width=True):
        st.session_state["page"] = "staff"
        st.rerun()
    if prev_staff and c_prev.button("⬅️ 前のスタッフ", key="go_prev_staff", use_container_width=True):
        st.session_state["editing_staff"] = prev_staff
        st.rerun()
    if next_staff and c_next.button("次のスタッフ ➡️", key="go_next_staff", use_container_width=True):
        st.session_state["editing_staff"] = next_staff
        st.rerun()

    st.markdown(
        """
        <style>
        div[data-testid="stMarkdown"]:has(#sd-shifts-marker) {
            display: none !important;
        }
        div:has(#sd-shifts-marker) + div span[data-baseweb="tag"] {
            background-color: rgba(26,115,232,.10) !important;
            border: 1px solid rgba(26,115,232,.20) !important;
        }
        div:has(#sd-shifts-marker) + div span[data-baseweb="tag"] span {
            color: #1A73E8 !important;
        }
        /* Hope Shifts (Yellow) */
        div[data-testid="stMarkdown"]:has(#sd-hopes-marker) {
            display: none !important;
        }
        div:has(#sd-hopes-marker) + div span[data-baseweb="tag"] {
            background-color: #FFF9C4 !important;
            border: 1px solid #FBC02D !important;
        }
        div:has(#sd-hopes-marker) + div span[data-baseweb="tag"] span {
            color: #202124 !important;
        }
        div:has(#sd-hopes-marker) + div span[data-baseweb="tag"],
        div:has(#sd-hopes-marker) + div span[data-baseweb="tag"] span {
            white-space: normal !important;
            max-width: none !important;
        }
        /* Rules (Yellow) */
        div[data-testid="stMarkdown"]:has(#sd-rules-marker) {
            display: none !important;
        }
        div:has(#sd-rules-marker) + div span[data-baseweb="tag"] {
            background-color: #FFF9C4 !important;
            border: 1px solid #FBC02D !important;
        }
        div:has(#sd-rules-marker) + div span[data-baseweb="tag"] span {
            color: #202124 !important;
        }
        /* NG Pairs (Yellow) */
        div[data-testid="stMarkdown"]:has(#sd-ng-marker) {
            display: none !important;
        }
        div:has(#sd-ng-marker) + div span[data-baseweb="tag"] {
            background-color: #FFF9C4 !important;
            border: 1px solid #FBC02D !important;
        }
        div:has(#sd-ng-marker) + div span[data-baseweb="tag"] span {
            color: #202124 !important;
        }
        /* Period Counts (Yellow) */
        div[data-testid="stMarkdown"]:has(#sd-pc-marker) {
            display: none !important;
        }
        div:has(#sd-pc-marker) + div span[data-baseweb="tag"] {
            background-color: #FFF9C4 !important;
            border: 1px solid #FBC02D !important;
        }
        div:has(#sd-pc-marker) + div span[data-baseweb="tag"] span {
            color: #202124 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.header(f"{target}さん の設定")

    df = st.session_state["staff_df"].copy()
    if "スタッフ名" not in df.columns or target not in df["スタッフ名"].astype(str).values:
        st.error("スタッフが見つかりません。")
        st.session_state["page"] = "staff"
        st.rerun()

    row_idx = df[df["スタッフ名"].astype(str) == target].index[0]
    row = df.loc[row_idx]

    with st.container(border=True):
        st.markdown('<div class="card-title" id="sd-basic-title">⚙️ 基本設定</div>', unsafe_allow_html=True)
        st.markdown('<span id="sd-basic-marker"></span>', unsafe_allow_html=True)
        
        # Employment Type Editor
        c_emp_lab, c_emp_sel = st.columns([3, 2])
        
        emp_opts = st.session_state.get("employment_types_list", ["正社員", "パート", "アルバイト"])
        curr_emp = str(row.get("雇用形態", ""))
        
        if curr_emp and curr_emp not in emp_opts:
            emp_opts = [curr_emp] + emp_opts
            
        idx = 0
        if curr_emp in emp_opts:
            idx = emp_opts.index(curr_emp)

        with c_emp_lab:
            st.markdown(
                "<div class='counter-label' style='font-size:1.2rem; height:44px; display:flex; align-items:center;'>雇用形態</div>",
                unsafe_allow_html=True,
            )
        new_emp = c_emp_sel.selectbox(
            "雇用形態",
            emp_opts,
            index=idx,
            key=f"sd_emp_{target}",
            label_visibility="collapsed",
        )
        df.at[row_idx, "雇用形態"] = new_emp

        max_cons = counter_input(
            "最大連勤数",
            int(row.get("最大連勤数", 0)),
            key=f"sd_max_{target}",
            label_size="1.2rem",
        )
        prev_cons = counter_input(
            "シフト開始前の連勤数",
            int(row.get("シフト開始前の連勤数", 0)),
            key=f"sd_prev_{target}",
            label_size="1.2rem",
        )
        st.caption("※ 0の場合は、初日から最大連勤数まで勤務可能です。")
        df.at[row_idx, "最大連勤数"] = max_cons
        df.at[row_idx, "シフト開始前の連勤数"] = prev_cons

        # 月・週回数設定が有効な休日について、入力欄を表示
        hol_props = st.session_state.get("holiday_properties", [])
        active_hols = st.session_state.get("holiday_types_list", [])
        target_hols = [p for p in hol_props if p.get("週回数固定設定") and p.get("名称") in active_hols]

        if target_hols:
            st.divider()
            st.markdown('<div class="sd-hol-caption">月・週の休日日数設定</div>', unsafe_allow_html=True)
            for p in target_hols:
                h_name = p["名称"]
                col_week = f"週の{h_name}日数"
                col_month = f"月の{h_name}日数"
                col_period = f"{h_name}日数対象"
                current_week = int(row.get(col_week, 1))
                current_month = int(row.get(col_month, 4))
                current_period = str(row.get(col_period, "週")).strip() or "週"
                period_idx = 0 if current_period == "週" else 1
                c_sel, c_val = st.columns([1, 2])
                period = c_sel.selectbox(
                    f"{h_name}の対象",
                    ["週", "月"],
                    index=period_idx,
                    key=f"sd_hol_period_{target}_{h_name}",
                )
                df.at[row_idx, col_period] = period
                if period == "週":
                    new_week = counter_input(
                        f"週の「{h_name}」日数",
                        current_week,
                        key=f"sd_hol_week_{target}_{h_name}",
                        label_size="1.1rem",
                        max_value=7,
                    )
                    df.at[row_idx, col_week] = new_week
                else:
                    new_month = counter_input(
                        f"月の「{h_name}」日数",
                        current_month,
                        key=f"sd_hol_month_{target}_{h_name}",
                        label_size="1.1rem",
                        max_value=31,
                    )
                    df.at[row_idx, col_month] = new_month

    with st.container(border=True):
        st.markdown('<div class="card-title">🧩 可能なシフト</div>', unsafe_allow_html=True)
        ws_list = st.session_state.get("work_shifts_list", [])
        ws_props = {p["名称"]: p for p in st.session_state.get("work_shift_properties", [])}
        target_ws_list = [ws for ws in ws_list if ws_props.get(ws, {}).get("必要人数対象", True)]
        current_able = [ws for ws in target_ws_list if bool(row.get(ws, True))]
        st.markdown('<span id="sd-shifts-marker"></span>', unsafe_allow_html=True)
        selected = st.multiselect(" ", target_ws_list, default=current_able, key=f"sd_shifts_{target}")
        for ws in target_ws_list:
            df.at[row_idx, ws] = (ws in selected)
        if selected:
            st.caption("各シフトの希望度（低 / 中 / 高）")
            pref_opts = ["高", "中", "低"]
            for ws in selected:
                pref_col = f"{ws}希望度"
                current_pref = str(row.get(pref_col, "中")).strip() or "中"
                if current_pref not in pref_opts:
                    current_pref = "中"
                pref_val = st.selectbox(
                    f"{ws} の希望度",
                    pref_opts,
                    index=pref_opts.index(current_pref),
                    key=f"sd_pref_{target}_{ws}",
                )
                df.at[row_idx, pref_col] = pref_val

    with st.container(border=True):
        st.markdown('<div class="card-title">📝 希望シフト</div>', unsafe_allow_html=True)
        st.caption("「作成」画面の暫定シフト表でも希望シフトを設定できます。")
        hope_df = st.session_state["hope_df"].copy()
        if target not in hope_df.index:
            hope_df.loc[target] = ""

        days = st.session_state.get("days_list", [])
        if not days:
            st.info("期間を設定してください。")
        else:
            # --- Calendar Selection UI for Hope Shift ---
            st.caption("カレンダーから日付を選択して、希望（休み・出勤など）を追加します。")
            
            # 1. State Management for Calendar
            if "sd_cal_year" not in st.session_state:
                st.session_state["sd_cal_year"] = st.session_state.get("start_date", datetime.date.today()).year
                st.session_state["sd_cal_month"] = st.session_state.get("start_date", datetime.date.today()).month
            
            # 2. Month Navigation
            c_m_prev, c_m_label, c_m_next = st.columns([1, 3, 1])
            with c_m_prev:
                if st.button("◀ 前月", key="sd_cal_prev", use_container_width=True):
                    if st.session_state["sd_cal_month"] == 1:
                        st.session_state["sd_cal_month"] = 12
                        st.session_state["sd_cal_year"] -= 1
                    else:
                        st.session_state["sd_cal_month"] -= 1
                    st.rerun()
            with c_m_label:
                st.markdown(
                    f"<h4 style='text-align:center; margin:0; padding-top:5px;'>"
                    f"{st.session_state['sd_cal_year']}年 {st.session_state['sd_cal_month']}月</h4>",
                    unsafe_allow_html=True
                )
            with c_m_next:
                if st.button("翌月 ▶", key="sd_cal_next", use_container_width=True):
                    if st.session_state["sd_cal_month"] == 12:
                        st.session_state["sd_cal_month"] = 1
                        st.session_state["sd_cal_year"] += 1
                    else:
                        st.session_state["sd_cal_month"] += 1
                    st.rerun()

            # 3. Calendar Grid
            st.markdown('<div style="margin-top:10px;"></div>', unsafe_allow_html=True)
            cols = st.columns(7)
            wd_labels = ["月", "火", "水", "木", "金", "土", "日"]
            for i, lab in enumerate(wd_labels):
                color = "#5F6368"
                if lab == "土": color = "#1A73E8"
                if lab == "日": color = "#EA4335"
                cols[i].markdown(
                    f"<div style='text-align:center; color:{color}; font-weight:800; font-size:13px; margin-bottom:4px;'>{lab}</div>",
                    unsafe_allow_html=True
                )

            cal_weeks = calendar.monthcalendar(st.session_state["sd_cal_year"], st.session_state["sd_cal_month"])
            
            # Current Selection State
            if "sd_selected_date" not in st.session_state:
                st.session_state["sd_selected_date"] = st.session_state.get("start_date", datetime.date.today())
            
            # Prepare valid date check
            valid_days_set = set()
            day_map = st.session_state.get("day_map", {})
            for d_str, d_obj in day_map.items():
                valid_days_set.add(d_obj)

            for week in cal_weeks:
                cols = st.columns(7)
                for i, d in enumerate(week):
                    with cols[i]:
                        if d == 0:
                            st.write("")
                            continue
                        
                        try:
                            this_date = datetime.date(st.session_state["sd_cal_year"], st.session_state["sd_cal_month"], d)
                        except ValueError:
                            st.write("")
                            continue

                        is_active = (this_date in valid_days_set)
                        is_selected = (this_date == st.session_state["sd_selected_date"])
                        btn_type = "primary" if is_selected else "secondary"

                        if is_active:
                            # Show marker if hope shift exists
                            d_key_candidate = [k for k, v in day_map.items() if v == this_date]
                            has_hope = False
                            if d_key_candidate:
                                val = hope_df.at[target, d_key_candidate[0]]
                                if str(val).strip():
                                    has_hope = True
                            
                            label = f"{d}"
                            if has_hope:
                                label = f"{d} ★"

                            if st.button(label, key=f"sd_cal_btn_{this_date}", type=btn_type, use_container_width=True):
                                st.session_state["sd_selected_date"] = this_date
                                st.rerun()
                        else:
                            st.button(f"{d}", key=f"sd_cal_dis_{this_date}", disabled=True, use_container_width=True)

            # 4. Input Form for Selected Date
            st.divider()
            sel_date = st.session_state["sd_selected_date"]
            
            # Get formatted date string for DataFrame key
            sel_d_str = ""
            for k, v in day_map.items():
                if v == sel_date:
                    sel_d_str = k
                    break
            
            if sel_d_str:
                badge_cls = badge_class_for_daylabel(sel_d_str)
                st.markdown(
                    f'<div class="card-title">📅 選択中: <span class="badge {badge_cls}">{sel_d_str}</span></div>', 
                    unsafe_allow_html=True
                )
                
                # Current Setting Display
                current_val = str(hope_df.at[target, sel_d_str]).strip()
                if current_val:
                    st.info(f"現在の設定: **{current_val}**")
                else:
                    st.markdown("<div style='color:#5F6368; font-size:14px; margin-bottom:8px;'>設定なし</div>", unsafe_allow_html=True)

                t_sel = st.selectbox(
                    "希望内容",
                    ["休み(全般)", "出勤(全般)"]
                    + st.session_state.get("work_shifts_list", [])
                    + st.session_state.get("holiday_types_list", []),
                    key="sd_type",
                    label_visibility="collapsed"
                )
                
                if st.button("追加", use_container_width=True, key="sd_addhope"):
                    hope_df.at[target, sel_d_str] = t_sel
                    st.session_state["hope_df"] = hope_df
                    mark_auto_gen_needed("希望シフトを更新しました")
                    st.toast(f"{sel_d_str} を {t_sel} に設定しました", icon="✅")
                    time.sleep(0.5)
                    st.rerun()
            else:
                st.warning("期間外の日付が選択されています。")

            # 5. List of registered hopes (Existing logic, simplified)
            st.divider()
            hopes = hope_df.loc[target] if target in hope_df.index else pd.Series(dtype=str)
            active = hopes[hopes != ""].dropna()
            if not active.empty:
                st.caption("登録済み一覧 (×で削除)")
                st.markdown('<span id="sd-hopes-marker"></span>', unsafe_allow_html=True)
                
                active_list = [f"{d} : {val}" for d, val in active.items()]
                
                remained = st.multiselect(
                    "登録済みシフト",
                    options=active_list,
                    default=active_list,
                    key=f"sd_hopes_multi_{target}",
                    label_visibility="collapsed"
                )

                if len(remained) < len(active_list):
                    removed = set(active_list) - set(remained)
                    for item in removed:
                        d_key = item.split(" : ")[0]
                        hope_df.at[target, d_key] = ""
                    st.session_state["hope_df"] = hope_df
                    mark_auto_gen_needed("希望シフトを更新しました")
                    st.rerun()

        st.session_state["hope_df"] = hope_df

    with st.container(border=True):
        st.markdown('<div class="card-title">⚖️ 曜日別ルール</div>', unsafe_allow_html=True)
        st.caption("「毎週火曜は休み」「木曜は日勤固定」などのルールを設定します。")

        rules_df = st.session_state.get("individual_rules_df", pd.DataFrame(columns=["スタッフ名", "曜日", "希望内容", "ルールタイプ"]))

        # 入力フォーム
        c1, c2, c3 = st.columns(3)
        dow_opts = ["月", "火", "水", "木", "金", "土", "日", "全日"]
        target_opts = ["休み(全般)", "出勤(全般)"] + st.session_state.get("work_shifts_list", []) + st.session_state.get("holiday_types_list", [])

        with c1:
            r_dow = st.selectbox("曜日", dow_opts, key=f"rule_dow_{target}")
        with c2:
            r_target = st.selectbox("内容", target_opts, key=f"rule_target_{target}")
        with c3:
            r_type = st.selectbox("タイプ", ["固定", "不可"], key=f"rule_type_{target}")

        if st.button("追加", key=f"rule_add_{target}", use_container_width=True):
            new_rule = {
                "スタッフ名": target,
                "曜日": r_dow,
                "希望内容": r_target,
                "ルールタイプ": r_type
            }
            rules_df = pd.concat([rules_df, pd.DataFrame([new_rule])], ignore_index=True)
            st.session_state["individual_rules_df"] = rules_df
            st.rerun()

        current_rules = rules_df[rules_df["スタッフ名"] == target]
        if not current_rules.empty:
            st.divider()
            st.caption("登録済み (×で削除)")
            st.markdown('<span id="sd-rules-marker"></span>', unsafe_allow_html=True)

            rule_map = {}
            display_list = []
            for idx, row in current_rules.iterrows():
                label = f"{row['曜日']} : {row['希望内容']} ({row['ルールタイプ']})"
                if label not in display_list:
                    display_list.append(label)
                if label not in rule_map:
                    rule_map[label] = []
                rule_map[label].append(idx)

            remained = st.multiselect(
                "登録済みルール",
                options=display_list,
                default=display_list,
                key=f"sd_rules_multi_{target}",
                label_visibility="collapsed"
            )

            if len(remained) < len(display_list):
                removed_labels = set(display_list) - set(remained)
                indices_to_drop = []
                for lbl in removed_labels:
                    indices_to_drop.extend(rule_map[lbl])
                
                if indices_to_drop:
                    rules_df = rules_df.drop(indices_to_drop).reset_index(drop=True)
                    st.session_state["individual_rules_df"] = rules_df
                    st.rerun()

    with st.container(border=True):
        st.markdown('<div class="card-title">⚡ 組み合わせNG</div>', unsafe_allow_html=True)
        st.caption("このスタッフと同じ日に勤務させない設定です。")

        ng_list = st.session_state.get("ng_pairs", [])
        all_staff = [
            str(x).strip()
            for x in st.session_state["staff_df"]["スタッフ名"].values
            if str(x).strip() and str(x).strip() != target
        ]

        if not all_staff:
            st.caption("他のスタッフが登録されていません。")
        else:
            partner = st.selectbox("相手を選択", all_staff, key=f"ng_partner_sel_{target}")
            if st.button("追加", key=f"ng_add_btn_{target}", use_container_width=True):
                if partner:
                    already = False
                    for p in ng_list:
                        sA, sB = p["スタッフA"], p["スタッフB"]
                        if {sA, sB} == {target, partner}:
                            already = True
                            break
                    if not already:
                        ng_list.append({"スタッフA": target, "スタッフB": partner})
                        st.session_state["ng_pairs"] = ng_list
                        st.rerun()

        relevant_indices = [i for i, p in enumerate(ng_list) if p["スタッフA"] == target or p["スタッフB"] == target]

        if relevant_indices:
            st.divider()
            st.caption("登録済み (×で削除)")
            st.markdown('<span id="sd-ng-marker"></span>', unsafe_allow_html=True)

            ng_map = {}
            display_list = []
            for i in relevant_indices:
                p = ng_list[i]
                other = p["スタッフB"] if p["スタッフA"] == target else p["スタッフA"]
                label = f"NG相手: {other}"
                if label not in display_list:
                    display_list.append(label)
                if label not in ng_map:
                    ng_map[label] = []
                ng_map[label].append(i)

            remained = st.multiselect(
                "登録済みNG",
                options=display_list,
                default=display_list,
                key=f"sd_ng_multi_{target}",
                label_visibility="collapsed"
            )

            if len(remained) < len(display_list):
                removed_labels = set(display_list) - set(remained)
                indices_to_remove = []
                for lbl in removed_labels:
                    indices_to_remove.extend(ng_map[lbl])
                
                # インデックスが大きい順に削除
                indices_to_remove.sort(reverse=True)
                for idx in indices_to_remove:
                    if 0 <= idx < len(ng_list):
                        del ng_list[idx]
                
                st.session_state["ng_pairs"] = ng_list
                st.rerun()

    with st.container(border=True):
        st.markdown('<div class="card-title" id="sd-pc-title">🔢 期間内の回数指定</div>', unsafe_allow_html=True)
        st.markdown('<div class="sd-pc-caption">この期間（1ヶ月など）の中で、特定のシフトを入れる回数を指定します。</div>', unsafe_allow_html=True)

        p_counts = st.session_state.get("period_counts", {})
        if target not in p_counts:
            p_counts[target] = {}

        # Form
        c_type_lab, c_type_sel = st.columns([3, 2])
        all_opts = st.session_state.get("work_shifts_list", []) + st.session_state.get("holiday_types_list", [])
        
        with c_type_lab:
            st.markdown(
                "<div class='counter-label' style='font-size:1.2rem; height:44px; display:flex; align-items:center;'>シフト</div>",
                unsafe_allow_html=True,
            )
        sel_type = c_type_sel.selectbox(
            "シフト",
            all_opts,
            key=f"pc_type_{target}",
            label_visibility="collapsed",
        )

        current_pc_val = p_counts.get(target, {}).get(sel_type, 0)
        sel_count = counter_input(
            "回数",
            safe_int(current_pc_val, 0),
            key=f"pc_count_{target}",
            label_size="1.2rem",
            max_value=31,
        )

        c_btn = st.columns([1])[0]
        with c_btn:
            if st.button("設定", key=f"pc_add_{target}", use_container_width=True):
                p_counts[target][sel_type] = sel_count
                st.session_state["period_counts"] = p_counts
                st.rerun()

        # List
        current_pc = p_counts.get(target, {})
        if current_pc:
            st.divider()
            st.caption("設定済み (×で削除)")
            st.markdown('<span id="sd-pc-marker"></span>', unsafe_allow_html=True)
            
            # Using multiselect logic for deletion
            pc_list = [f"{k}: {v}回" for k, v in current_pc.items()]
            remained = st.multiselect(
                "設定済み回数",
                options=pc_list,
                default=pc_list,
                key=f"pc_multi_{target}",
                label_visibility="collapsed"
            )

            if len(remained) < len(pc_list):
                # Reconstruct dict based on remaining items
                new_pc = {}
                for item in remained:
                    # item format "ShiftName: N回"
                    parts = item.split(": ")
                    if len(parts) >= 2:
                        s_name = parts[0]
                        try:
                            c_val = int(parts[1].replace("回", ""))
                            new_pc[s_name] = c_val
                        except:
                            pass
                p_counts[target] = new_pc
                st.session_state["period_counts"] = p_counts
                st.rerun()

    st.session_state["staff_df"] = df


def page_req():
    st.header("要員配置")

    def template_row_for_day(day_label: str) -> pd.Series:
        day_map = st.session_state.get("day_map", {})
        d_obj = day_map.get(day_label)
        if not d_obj:
            return pd.Series({ws: 0 for ws in st.session_state.get("work_shifts_list", [])})

        w_key = WEEKDAYS_JP[d_obj.weekday()]

        wd_settings = st.session_state.get("req_by_weekday", pd.DataFrame())
        work_shifts_local = st.session_state.get("work_shifts_list", [])
        out = {}
        for ws in work_shifts_local:
            try:
                out[ws] = int(wd_settings.at[w_key, ws])
            except Exception:
                out[ws] = 0
        return pd.Series(out)

    def build_exceptions_df(req_df: pd.DataFrame) -> pd.DataFrame:
        days_list = st.session_state.get("days_list", [])
        work_shifts_local = st.session_state.get("work_shifts_list", [])
        rows = []
        for d in days_list:
            if d not in req_df.index:
                continue
            templ = template_row_for_day(d)
            curr = req_df.loc[d, work_shifts_local].copy()
            curr = curr.fillna(0).astype(int)
            templ = templ.fillna(0).astype(int)
            if not curr.equals(templ):
                row = {"日付": d}
                for ws in work_shifts_local:
                    row[ws] = int(curr.get(ws, 0))
                rows.append(row)
        if not rows:
            return pd.DataFrame(columns=["日付"] + work_shifts_local)
        return pd.DataFrame(rows)

    work_shifts = st.session_state.get("work_shifts_list", [])
    ws_props = {p["名称"]: p for p in st.session_state.get("work_shift_properties", [])}
    # 必要人数対象のシフトのみ抽出
    target_work_shifts = [ws for ws in work_shifts if ws_props.get(ws, {}).get("必要人数対象", True)]

    target_index = WEEKDAYS_JP
    wd_df = st.session_state.get("req_by_weekday", pd.DataFrame())
    wd_df = wd_df.reindex(index=target_index, columns=work_shifts, fill_value=0)
    st.session_state["req_by_weekday"] = wd_df

    tab1, tab2 = st.tabs(["基本要員配置（曜日別）", "日別配置調整"])

    with tab1:
        st.caption("曜日ごとの基本配置数を設定します。「基本設定を全期間に反映」でカレンダー全体に適用されます。")

        if st.button("基本設定を全期間に反映", key="apply_basic_to_all", use_container_width=True):
            days_list = st.session_state.get("days_list", [])
            req_df_curr = st.session_state["req_df"]
            # 全期間に対してtemplate_row_for_dayを適用
            for d in days_list:
                if d in req_df_curr.index:
                    templ = template_row_for_day(d)
                    # 全シフト項目を上書き
                    for col in req_df_curr.columns:
                        if col in templ.index:
                            req_df_curr.at[d, col] = int(templ[col])
            st.session_state["req_df"] = req_df_curr
            st.success("基本設定を全期間に反映しました。（日別の例外設定は上書きされました）")

        wd_df = st.session_state["req_by_weekday"]
        weekdays_all = WEEKDAYS_JP

        if "req_wd_idx" not in st.session_state:
            st.session_state["req_wd_idx"] = 0

        # 曜日選択ボタン（7つ並べる）
        st.markdown('<div style="margin-top:10px; margin-bottom:10px;"></div>', unsafe_allow_html=True)
        wd_cols = st.columns(7)
        for i, w_label in enumerate(weekdays_all):
            is_sel = (i == st.session_state["req_wd_idx"])
            btn_type = "primary" if is_sel else "secondary"
            # 見やすくするためにボタンの文字を強調などしたいが、標準ボタンで十分大きい
            if wd_cols[i].button(w_label, key=f"wd_sel_btn_{i}", type=btn_type, use_container_width=True):
                st.session_state["req_wd_idx"] = i
                st.rerun()
        
        selected_wd = weekdays_all[st.session_state["req_wd_idx"]]

        badge_cls = badge_class_for_weekday(selected_wd)
        with st.container(border=True):
            st.markdown(
                f'<div class="card-title" style="text-align:center; font-size:1.5rem; margin-bottom:1rem; display:flex; justify-content:center; align-items:center; gap:10px;">📌 曜日別基本設定 <span class="badge {badge_cls}" style="font-size:2.5rem; padding:5px 20px;">{selected_wd}</span></div>',
                unsafe_allow_html=True,
            )

            changed = False
            for ws in target_work_shifts:
                cur = int(wd_df.at[selected_wd, ws]) if (selected_wd in wd_df.index and ws in wd_df.columns) else 0
                new = counter_input(ws, cur, key=f"wdcnt_{selected_wd}_{ws}", label_size="1.3rem")
                if new != cur:
                    wd_df.at[selected_wd, ws] = new
                    changed = True

            if changed:
                st.session_state["req_by_weekday"] = wd_df

    with tab2:
        st.caption("特定の日付の配置数を調整します。基本設定と異なる日のみが表示されます。")

        req_df = st.session_state["req_df"]
        days = st.session_state.get("days_list", [])
        if not days:
            st.info("期間を設定してください。")
            return

        exceptions_df = build_exceptions_df(req_df)
        ex_count = 0 if exceptions_df.empty else len(exceptions_df)
        # 表示用にカラムを絞る
        display_cols = ["日付"] + target_work_shifts

        with st.container(border=True):
            # Header
            c_head_title, c_head_badge = st.columns([1, 4])
            st.markdown(
                f'<div class="card-title" style="margin-bottom:0;">🛠️ 例外設定リスト <span class="badge yellow" style="margin-left:8px;">{ex_count}</span></div>',
                unsafe_allow_html=True,
            )
            
            if exceptions_df.empty:
                st.markdown('<div style="margin-top:12px;"></div>', unsafe_allow_html=True)
                st.success("例外設定はありません。（すべて基本通り）")
            else:
                st.caption("曜日ごとの基本ルールと異なる設定の日付一覧です。")
                st.markdown('<div style="margin-top:12px;"></div>', unsafe_allow_html=True)

                # Card Style List
                for i, row in exceptions_df.iterrows():
                    d_str = row["日付"]
                    templ = template_row_for_day(d_str).fillna(0).astype(int)
                    
                    with st.container(border=True):
                        # Row 1: Date and Actions
                        c_top_date, c_top_spacer, c_top_edit, c_top_reset = st.columns([2, 1, 1, 1])
                        
                        with c_top_date:
                            st.markdown(f"#### {d_str}")
                        
                        with c_top_edit:
                            if st.button("編集", key=f"edit_btn_{d_str}", use_container_width=True):
                                if d_str in days:
                                    st.session_state["req_day_idx"] = days.index(d_str)
                                    st.rerun()
                        
                        with c_top_reset:
                            if st.button("解除", key=f"reset_btn_{d_str}", type="secondary", use_container_width=True):
                                new_req = st.session_state["req_df"].copy()
                                if d_str in new_req.index:
                                    for ws_key in target_work_shifts:
                                        new_req.at[d_str, ws_key] = int(templ.get(ws_key, 0))
                                    st.session_state["req_df"] = new_req
                                    st.toast(f"{d_str} をリセットしました", icon="🗑️")
                                    time.sleep(0.5)
                                    st.rerun()
                        
                        # Row 2: Changes content
                        diff_texts = []
                        for ws in target_work_shifts:
                            actual = int(row.get(ws, 0))
                            standard = int(templ.get(ws, 0))
                            if actual != standard:
                                diff_texts.append(f"**{ws}**: {standard} → <span style='color:#D93025; font-weight:bold;'>{actual}</span>")
                        
                        if diff_texts:
                            st.markdown("  \n".join([f"- {t}" for t in diff_texts]), unsafe_allow_html=True)
                        else:
                            st.caption("変更なし")

                # Bottom Action
                st.markdown('<div style="margin-top:16px;"></div>', unsafe_allow_html=True)
                if st.button("設定をすべてリセット", key="reset_all_list", type="primary", use_container_width=True):
                    req_df = st.session_state["req_df"].copy()
                    for d_str in req_df.index:
                        templ2 = template_row_for_day(d_str)
                        for col in req_df.columns:
                            if col in templ2.index:
                                req_df.at[d_str, col] = int(templ2[col])
                    st.session_state["req_df"] = req_df
                    st.success("リセットしました。")
                    time.sleep(1.0)
                    st.rerun()

        st.divider()

        if "req_day_idx" not in st.session_state:
            st.session_state["req_day_idx"] = 0
        if st.session_state["req_day_idx"] >= len(days):
            st.session_state["req_day_idx"] = 0

        # Current selection
        current_day_str = days[st.session_state["req_day_idx"]]
        day_map = st.session_state.get("day_map", {})
        current_date_obj = day_map.get(current_day_str)
        if not current_date_obj:
            current_date_obj = st.session_state.get("start_date", datetime.date.today())

        # View state for calendar (Year/Month)
        if "cal_view_year" not in st.session_state:
            st.session_state["cal_view_year"] = current_date_obj.year
            st.session_state["cal_view_month"] = current_date_obj.month

        # --- Custom Calendar UI ---
        st.markdown(
            """
            <div style="background-color:#E8F0FE; border-left:5px solid #1A73E8; padding:12px; border-radius:4px; margin-bottom:12px;">
                <span style="font-weight:bold; color:#1A73E8;">📅 Step 1. 日付を選択</span><br>
                下のカレンダーから日付をクリックして、その日の人数設定を開いてください。
            </div>
            """,
            unsafe_allow_html=True
        )
        # Month Navigation
        c_m_prev, c_m_label, c_m_next = st.columns([1, 3, 1])
        with c_m_prev:
            if st.button("◀ 前月", key="cal_prev_month", use_container_width=True):
                if st.session_state["cal_view_month"] == 1:
                    st.session_state["cal_view_month"] = 12
                    st.session_state["cal_view_year"] -= 1
                else:
                    st.session_state["cal_view_month"] -= 1
                st.rerun()
        
        with c_m_label:
            st.markdown(
                f"<h3 style='text-align:center; margin:0; padding-top:5px;'>"
                f"{st.session_state['cal_view_year']}年 {st.session_state['cal_view_month']}月</h3>",
                unsafe_allow_html=True
            )
        
        with c_m_next:
            if st.button("翌月 ▶", key="cal_next_month", use_container_width=True):
                if st.session_state["cal_view_month"] == 12:
                    st.session_state["cal_view_month"] = 1
                    st.session_state["cal_view_year"] += 1
                else:
                    st.session_state["cal_view_month"] += 1
                st.rerun()

        # Day Grid Header
        st.markdown('<div style="margin-top:10px;"></div>', unsafe_allow_html=True)
        cols = st.columns(7)
        wd_labels = ["月", "火", "水", "木", "金", "土", "日"]
        for i, lab in enumerate(wd_labels):
            color = "#5F6368"
            if lab == "土": color = "#1A73E8"
            if lab == "日": color = "#EA4335"
            cols[i].markdown(
                f"<div style='text-align:center; color:{color}; font-weight:800; font-size:13px; margin-bottom:4px;'>{lab}</div>",
                unsafe_allow_html=True
            )

        # Day Grid Body
        cal_weeks = calendar.monthcalendar(st.session_state["cal_view_year"], st.session_state["cal_view_month"])
        
        # Prepare reverse map for fast lookup: date -> index in `days`
        date_to_idx = {}
        for idx, d_str in enumerate(days):
            if d_str in day_map:
                date_to_idx[day_map[d_str]] = idx

        for week in cal_weeks:
            cols = st.columns(7)
            for i, d in enumerate(week):
                with cols[i]:
                    if d == 0:
                        st.write("")
                        continue
                    
                    try:
                        this_date = datetime.date(st.session_state["cal_view_year"], st.session_state["cal_view_month"], d)
                    except ValueError:
                        st.write("")
                        continue

                    # Determine button style and state
                    target_idx = date_to_idx.get(this_date)
                    is_active = (target_idx is not None)
                    is_selected = (this_date == current_date_obj)
                    
                    btn_type = "primary" if is_selected else "secondary"
                    
                    # If the date is valid for this shift period, make it clickable
                    if is_active:
                        # Mark days with modified settings? (Optional improvement)
                        # We can check if it's an exception (in exceptions_df logic)
                        # For now, just keep it simple as requested.
                        if st.button(f"{d}", key=f"cal_btn_{this_date}", type=btn_type, use_container_width=True):
                            st.session_state["req_day_idx"] = target_idx
                            st.rerun()
                    else:
                        # Out of range (not in `days`) -> Disabled
                        st.button(f"{d}", key=f"cal_btn_dis_{this_date}", disabled=True, use_container_width=True)
        
        st.markdown('<div style="margin-bottom:20px;"></div>', unsafe_allow_html=True)

        selected_day = days[st.session_state["req_day_idx"]]

        templ = template_row_for_day(selected_day).fillna(0).astype(int)
        curr = req_df.loc[selected_day, work_shifts].fillna(0).astype(int) if selected_day in req_df.index else templ.copy()
        is_exception = not curr.equals(templ)

        badge_cls = badge_class_for_daylabel(selected_day)
        ex_badge = '<span class="badge red">変更あり</span>' if is_exception else '<span class="badge green">基本設定通り</span>'

        with st.container(border=True):
            st.markdown(
                f'<div class="card-title">📅 日別設定 <span class="badge {badge_cls}">{selected_day}</span> {ex_badge}</div>',
                unsafe_allow_html=True,
            )

            updated_single = False
            for ws in target_work_shifts:
                curv = int(curr.get(ws, 0))
                newv = counter_input(ws, curv, key=f"daycnt_{selected_day}_{ws}")
                if newv != curv:
                    req_df.at[selected_day, ws] = newv
                    updated_single = True

            if updated_single:
                st.session_state["req_df"] = req_df
                st.rerun()

            if st.button("基本設定に戻す", key="reset_day_to_template", use_container_width=True):
                new_req = st.session_state["req_df"].copy()
                for ws in target_work_shifts:
                    new_req.at[selected_day, ws] = int(templ.get(ws, 0))
                st.session_state["req_df"] = new_req
                st.success("基本設定に戻しました")
                time.sleep(0.15)
                st.rerun()

        with st.expander("基本設定との差分を見る", expanded=False):
            comp = pd.DataFrame([templ[target_work_shifts], curr[target_work_shifts]], index=["基本設定", "現在"]).astype(int)
            st.dataframe(comp, use_container_width=True)




def page_gen():
    st.header("シフト作成")

    start = st.session_state.get("start_date")
    end = st.session_state.get("end_date")
    if isinstance(start, datetime.date) and isinstance(end, datetime.date) and end >= start:
        days, day_map = compute_days(start, end)
        st.session_state["days_list"] = days
        st.session_state["day_map"] = day_map
    else:
        days, day_map = [], {}

    # Provisional schedule table (based on hopes and weekday rules)
    with st.container(border=True):
        st.markdown('<div class="card-title">🧭 暫定シフト表（現時点）</div>', unsafe_allow_html=True)
        st.caption("希望シフト・曜日別ルールを反映した暫定表です。編集すると希望シフトに反映されます。")

        if not days:
            st.info("期間を設定してください。")
        else:
            staff_df = st.session_state.get("staff_df", pd.DataFrame(columns=["スタッフ名"]))
            hope_df = st.session_state.get("hope_df", pd.DataFrame())
            rules_df = st.session_state.get("individual_rules_df", pd.DataFrame())

            provisional_df = build_provisional_table(days, day_map, staff_df, hope_df, rules_df)

            with st.container():
                all_shifts = ["休み(全般)", "出勤(全般)"] + st.session_state.get("work_shifts_list", []) + st.session_state.get("holiday_types_list", []) + ["削除"]
                c_config = {"スタッフ名": st.column_config.TextColumn("スタッフ名", disabled=True)}
                for col in days:
                    c_config[col] = st.column_config.SelectboxColumn(col, options=all_shifts, required=False, width="small")

                st.caption("⬇️ 編集ビュー（プレビューと同じ配色）")
                st.markdown(render_shift_table_html(provisional_df), unsafe_allow_html=True)

                st.caption("編集するセルを選んで適用してください。")
                staff_opts = provisional_df["スタッフ名"].astype(str).tolist()
                c_s, c_d, c_v = st.columns([2, 2, 3])
                with c_s:
                    sel_staff = st.selectbox("スタッフ", staff_opts, key="prov_edit_staff")
                with c_d:
                    sel_day = st.selectbox("日付", days, key="prov_edit_day")
                with c_v:
                    sel_val = st.selectbox("シフト", all_shifts, key="prov_edit_shift")

                curr_val = ""
                if sel_staff in provisional_df["スタッフ名"].values:
                    row = provisional_df[provisional_df["スタッフ名"] == sel_staff]
                    if not row.empty and sel_day in row.columns:
                        curr_val = str(row.iloc[0].get(sel_day, "")).strip()
                st.caption(f"現在の値: {curr_val or '未設定'}")

                if st.button("追加", key="prov_apply_cell", use_container_width=True):
                    if sel_staff not in hope_df.index:
                        hope_df.loc[sel_staff] = ""
                    hope_df.at[sel_staff, sel_day] = "" if sel_val == "削除" else sel_val
                    st.session_state["hope_df"] = hope_df
                    mark_auto_gen_needed("希望シフトを更新しました")
                    st.toast("希望シフトに反映しました", icon="✅")
                    st.rerun()

    with st.container(border=True):
        st.markdown('<div class="card-title">🚀 生成</div>', unsafe_allow_html=True)
        st.caption("現在の設定でシフトを生成します。")
        if st.button("生成開始", type="primary", use_container_width=True, key="gen_start"):
            if not isinstance(start, datetime.date) or not isinstance(end, datetime.date) or end < start:
                st.error("期間設定が不正です。")
            else:
                ws = st.session_state.get("work_shifts_list", [])
                hol = st.session_state.get("holiday_types_list", [])
                shift_types = hol + ws

                result_df, debug_msgs = run_and_store_generation(
                    days, day_map, ws, hol, shift_types, trigger="manual", reason="生成開始"
                )
                if result_df is not None:
                    if debug_msgs:
                        with st.expander("⚠️ 結果に関するお知らせ（不足・余剰など）", expanded=True):
                            for msg in debug_msgs:
                                st.write(msg)
                else:
                    st.error("解が見つかりませんでした。条件を緩和してください。")
                    if debug_msgs:
                        with st.expander("詳細な理由（可能性）", expanded=True):
                            for msg in debug_msgs:
                                st.write(msg)

    if st.session_state.get("last_result") is not None:
        st.subheader("作成結果")
        
        # 修正モードは常に表示
        res = st.session_state["last_result"]
        all_shifts = st.session_state.get("work_shifts_list", []) + st.session_state.get("holiday_types_list", [])

        # 列設定: スタッフ名は編集不可、それ以外（日付列）はセレクトボックス
        c_config = {}
        c_config["スタッフ名"] = st.column_config.TextColumn("スタッフ名", disabled=True)
        for col in res.columns:
            if col != "スタッフ名":
                c_config[col] = st.column_config.SelectboxColumn(
                    col,
                    options=all_shifts,
                    required=True,
                    width="small"
                )

        st.markdown(render_shift_table_html(res), unsafe_allow_html=True)

        st.info("編集するセルを選んで修正してください。")
        staff_opts = res["スタッフ名"].astype(str).tolist()
        days_opts = [c for c in res.columns if c != "スタッフ名"]
        c_s, c_d, c_v = st.columns([2, 2, 3])
        with c_s:
            sel_staff = st.selectbox("スタッフ", staff_opts, key="result_edit_staff")
        with c_d:
            sel_day = st.selectbox("日付", days_opts, key="result_edit_day")
        with c_v:
            sel_val = st.selectbox("シフト", all_shifts, key="result_edit_shift")

            curr_val = ""
            row = res[res["スタッフ名"] == sel_staff]
            if not row.empty and sel_day in row.columns:
                curr_val = str(row.iloc[0].get(sel_day, "")).strip()
            st.caption(f"現在の値: {curr_val or '未設定'}")

        if st.button("追加", key="result_apply_cell", use_container_width=True):
            res.loc[res["スタッフ名"] == sel_staff, sel_day] = sel_val
            st.session_state["last_result"] = res
            st.toast("結果に反映しました", icon="✅")
            st.rerun()

        # CSVダウンロード（共通）
        res_final = st.session_state["last_result"]
        # ダウンロードセクション
        st.subheader("💾 ファイル保存")
        c_dl_1, c_dl_2 = st.columns(2)

        # 1. CSV
        res_final = st.session_state["last_result"]
        csv = res_final.to_csv(index=False).encode("utf-8-sig")
        c_dl_1.download_button("📄 CSVで保存", csv, "shift.csv", "text/csv", use_container_width=True, key="dl_csv")

        # 2. HTML (見やすい表)
        html_table = render_shift_table_html(res_final, for_export=True)
        html_content = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: sans-serif; padding: 20px; }}
                h2 {{ color: #202124; }}
                table {{ border-collapse: collapse; width: 100%; font-size: 13px; }}
                th, td {{ border: 1px solid #E0E3E7; padding: 8px; text-align: center; }}
                th {{ background: #F8F9FA; }}
            </style>
        </head>
        <body>
            <h2>シフト表</h2>
            {html_table}
        </body>
        </html>
        """
        c_dl_2.download_button("🌐 表(HTML)で保存", html_content, "shift_table.html", "text/html", use_container_width=True, key="dl_html")


# ----------------------------
# Main App Loop
# ----------------------------
def main():
    if "current_user" not in st.session_state:
        render_login()
        return

    if not st.session_state.get("data_loaded", False):
        load_user_json(st.session_state["current_user"])
        st.session_state["data_loaded"] = True

    ensure_core_defaults()

    start = st.session_state.get("start_date", datetime.date.today())
    end = st.session_state.get("end_date", datetime.date.today() + datetime.timedelta(days=30))
    if not isinstance(start, datetime.date):
        start = datetime.date.today()
        st.session_state["start_date"] = start
    if not isinstance(end, datetime.date):
        end = start + datetime.timedelta(days=30)
        st.session_state["end_date"] = end

    if end < start:
        end = start
        st.session_state["end_date"] = end

    days, day_map = compute_days(start, end)
    st.session_state["days_list"] = days
    st.session_state["day_map"] = day_map

    sync_staff_df_schema()
    sync_req_df(days)
    sync_hope_df(days)

    maybe_flag_auto_generation()
    maybe_run_auto_generation()

    render_navbar()
    page = st.session_state.get("page", "home")

    if page == "home":
        page_home()
    elif page == "staff":
        page_staff()
    elif page == "staff_detail":
        page_staff_detail()
    elif page == "req":
        page_req()
    elif page == "gen":
        page_gen()
    elif page == "save_load":
        page_save_load()
    else:
        st.session_state["page"] = "home"
        st.rerun()

    autosave_user_json(st.session_state["current_user"])


if __name__ == "__main__":
    main()
