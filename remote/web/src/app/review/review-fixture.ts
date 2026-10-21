export const reviewFixture = {
  run: "REQ-027",
  task: "T15c",
  attempt: "att-0019",
  cause: "La verificación falló al ejecutar las comprobaciones del proyecto.",
  verificationOutput: "$ npm run verify\n> lint\nError: no se pudo completar la verificación\nExit code: 1",
  diffStat: "remote/web/src/app/review/page.tsx | 1 +\n1 file changed, 1 insertion(+)",
  logTail: "[12:02:34] Iniciando verificación\n[12:02:35] Ejecutando lint\n[12:02:36] Error: no se pudo completar la verificación\n[12:02:36] Verificación finalizada con código 1",
};
