"""Contract conservation checks over the reviewed full-file resolutions."""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SESSION=Path('/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/RUN.solver/20261030-120814-28ad')
requests=[t['resolution'] for t in json.loads((SESSION/'triggers.json').read_text()) if t.get('resolution')]
for r in requests:
 text=(ROOT/'reviewed'/(r['key']+'.resolved')).read_text();p=r['path']
 if p in ['src/app/page.tsx','src/app/asistente/page.tsx','src/app/login/page.tsx','src/lib/cuentas/cuenta-actual.ts']:
  assert 'resolveServer' in text and 'const session = await resolveServer' in text,p
  assert 'SESSION_COOKIE' not in text and 'resolverSesion' not in text,p
 if p=='src/app/page.tsx':
  assert '<PortadaHerramientas permissions={session.permissions} roles={session.roles} language={await getRequestLanguage()}' in text
  assert 'if (!session) redirect("/login")' in text
  assert 'InicioChat' not in text and 'InicioCliente' not in text
 if p in ['src/app/login/page.tsx','src/app/asistente/page.tsx']:
  assert 'getRequestLanguage()' in text and 'redirect(' in text,p
  assert 'language={language}' in text,p
 if p=='src/lib/cuentas/cuenta-actual.ts':
  assert 'permissions: session.permissions' in text and 'dataNoticeVersion: VERSION_AVISO_DATOS' in text
  assert 'getAccountLanguage' not in text
  assert 'language: null' in text
 if p=='src/components/ui/shell/CabeceraApp.tsx':
  assert 'const copy = textosHerramientas(language)' in text
  assert 'copy.statistics' in text and 'copy.laboratory' in text
  assert ('tienePermiso(PERMISOS.herramientas_internas)' in text or 'esDev && puedeVerAdministracion' in text)
  assert 'href: "/"' not in text,'Do not restore retired classic-chat navigation'
  assert 'href: "/3d"' not in text and 'href: "/catalogo"' not in text,'Keep centralized tool navigation'
 if p=='src/components/guiado/VistaGuiada.tsx':
  assert 'permisos?: readonly string[]' in text and '<CabeceraApp permisos={permisos} language={language}' in text
 if p=='src/app/3d/Taller3DConPermisoPersonal.tsx':
  assert 'getRequestLanguage()' in text and 'puedeExplorarDecoraciones(session.permissions)' in text
  assert 'decoracionEntrada={decoracion}' in text and 'canViewOtherAccounts={canViewOtherAccounts}' in text
 if p=='scripts/test/test-harness-taller-esenciales.ts':
  assert 'resolverBlender({ NODE_ENV: "test" }, root)' in text
  assert text.count('assert.')==(ROOT/'review'/(r['key']+'.ours')).read_text().count('assert.')
 if p=='scripts/test/test-integracion-proyectos.ts':
  assert 'error.code === "CUENTA_CON_TRABAJO"' in text and 'retainedOwner.rowCount, 1' in text
 if p=='scripts/test/test-integracion-decoraciones-personales.ts':
  assert '"Biblioteca del Taller"' in text and '"taller3d:escena:trabajo:v1"' in text
  assert text.count('assert.')==(ROOT/'review'/(r['key']+'.ours')).read_text().count('assert.')
 if p.endswith('.json'):
  doc=json.loads(text);old=json.loads((ROOT/'review'/(r['key']+'.ours')).read_text());new=json.loads((ROOT/'review'/(r['key']+'.theirs')).read_text())
  assert doc.pop('previousObservations')==[{'sourceBlob':r['blobs']['ours'],'evidence':old}]
  assert doc==new and doc['status']=='blocked'
print('All 17 reviewed unions preserve their declared contract invariants.')
