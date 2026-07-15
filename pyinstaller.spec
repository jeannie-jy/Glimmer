# -*- mode: python ; coding: utf-8 -*-
a = Analysis(
    ['server/main.py'],
    pathex=[],
    binaries=[],
    datas=[('harness', 'harness'), ('server', 'server'), ('.harness', '.harness')],
    hiddenimports=['harness', 'harness.models', 'harness.llm', 'harness.tools', 'harness.guardrails', 'harness.feedback', 'harness.memory', 'harness.config', 'harness.credentials', 'server', 'server.api'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'pandas'],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='lite-agent-harness',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)
