"""Throwaway fixtures for the eval runs: tiny git repos + an isolated bitácora root.

Everything is created under the run directory (inside %TEMP%), never under the real ~/bitacora or ~/metodologia.
Remotes are local bare clones next to the repo, so even an unwanted `git push` can't leave the machine.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent / "skill"
BITACORA_PY = SKILL / "scripts" / "bitacora.py"


def git(cwd: Path, *args: str) -> str:
    res = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    if res.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed in {cwd}: {res.stderr.strip()}")
    return res.stdout.strip()


def _write(root: Path, files: dict[str, str]) -> None:
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8", newline="\n")


def _init_repo(repo: Path, remote_name: str) -> None:
    """git init + first commit + a local bare clone as `origin` (created with clone, not push)."""
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "evals@localhost")
    git(repo, "config", "user.name", "evals")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "chore: initial fixture")
    bare = repo.parent / f"{remote_name}.git"
    git(repo.parent, "clone", "-q", "--bare", str(repo), str(bare))
    git(repo, "remote", "add", "origin", bare.as_posix())
    git(repo, "fetch", "-q", "origin")
    git(repo, "branch", "-q", "--set-upstream-to=origin/main", "main")


# ---------------------------------------------------------------- next-app (English identifiers)

def _orders_ts(lines: int = 520) -> str:
    out = [
        "// Order helpers for the store. Grew organically; one module for everything order-related.",
        "export type OrderStatus = 'pending' | 'paid' | 'shipped' | 'delivered';",
        "",
        "export interface Order {",
        "  id: string;",
        "  status: OrderStatus;",
        "  items: { sku: string; qty: number; price: number }[];",
        "  createdAt: Date;",
        "}",
        "",
    ]
    i = 0
    while len(out) + 9 <= lines:  # whole functions only; pad the rest with section comments
        i += 1
        out += [
            f"export function orderMetric{i}(order: Order): number {{",
            f"  // metric {i}: weighted item total",
            "  let total = 0;",
            "  for (const item of order.items) {",
            f"    total += item.qty * item.price * {1 + (i % 7) / 100};",
            "  }",
            "  return Math.round(total * 100) / 100;",
            "}",
            "",
        ]
    out += [f"// metric {n}: reserved" for n in range(i + 1, i + 1 + lines - len(out))]
    return "\n".join(out) + "\n"


NEXT_APP = {
    "package.json": '{\n  "name": "tienda-web",\n  "private": true,\n  "scripts": {"dev": "next dev", "build": "next build"},\n'
                    '  "dependencies": {"next": "15.0.0", "react": "19.0.0", "react-dom": "19.0.0"}\n}\n',
    "README.md": "# tienda-web\n\nOnline store frontend (Next.js App Router). Products, cart and checkout.\n\n"
                 "- `src/app` routes · `src/components` UI · `src/lib` domain helpers\n"
                 "- Deployed with docker compose on the VPS (see the project's TOOLS.md).\n",
    "tsconfig.json": '{ "compilerOptions": { "strict": true, "jsx": "preserve" } }\n',
    "src/app/layout.tsx": "import { Header } from '../components/Header';\n\n"
                          "export default function RootLayout({ children }: { children: React.ReactNode }) {\n"
                          "  return (<html lang=\"es\"><body><Header />{children}</body></html>);\n}\n",
    "src/app/page.tsx": "import { ProductCard } from '../components/ProductCard';\nimport { products } from '../lib/products';\n\n"
                        "export default function Home() {\n  return (<main>{products.map((p) => <ProductCard key={p.id} product={p} />)}</main>);\n}\n",
    "src/components/Header.tsx": "export function Header() {\n  return (\n    <header>\n      <a href=\"/\">Tienda</a>\n"
                                 "      <button>Buy now</button>\n    </header>\n  );\n}\n",
    "src/components/ProductCard.tsx": (
        "'use client';\nimport { useEffect, useState } from 'react';\nimport type { Product } from '../lib/products';\n\n"
        "export function ProductCard({ product }: { product: Product }) {\n"
        "  const [stock, setStock] = useState(product.stock);\n"
        "  // refresh stock from the API\n"
        "  useEffect(() => { fetch(`/api/stock/${product.id}`).then((r) => r.json()).then((d) => setStock(d.stock)); });\n"
        "  return (\n    <article>\n      <h2>{product.name}</h2>\n"
        "      <p>${(product.price / 100).toFixed(2)}</p>\n      <small>{stock} in stock</small>\n    </article>\n  );\n}\n"),
    "src/components/Cart.tsx": "export function Cart({ total }: { total: number }) {\n"
                               "  return (<aside><h3>Cart</h3><p>Totla: {total}</p></aside>);\n}\n",
    "src/lib/products.ts": "export interface Product { id: string; name: string; price: number; stock: number }\n\n"
                           "export const products: Product[] = [\n  { id: 'p1', name: 'Mug', price: 2500, stock: 3 },\n"
                           "  { id: 'p2', name: 'Poster', price: 1500, stock: 0 },\n];\n",
    "src/lib/stock.ts": (
        "import type { Product } from './products';\n\n"
        "export function isOutOfStock(product: Product): boolean {\n  return product.stock <= 0;\n}\n\n"
        "// FIXME: no validation, negative quantities allowed and nothing is persisted\n"
        "export function restock(product: Product, qty: number): Product {\n"
        "  console.log('restock', product.id, qty);\n  return { ...product, stock: product.stock + qty };\n}\n"),
    "src/lib/orders.ts": _orders_ts(520),
}

# ---------------------------------------------------------------- pedidos-api (Spanish identifiers)

ES_REPO = {
    "package.json": '{\n  "name": "pedidos-api",\n  "private": true,\n  "scripts": {"test": "vitest run"}\n}\n',
    "README.md": "# pedidos-api\n\nServicio de pedidos de la distribuidora. Calcula totales y descuentos.\n",
    "src/pedidos.ts": (
        "export interface LineaPedido { producto: string; cantidad: number; precioUnitario: number }\n\n"
        "export interface Pedido { id: string; cliente: string; lineas: LineaPedido[]; descuento: number }\n\n"
        "export function calcularSubtotal(pedido: Pedido): number {\n"
        "  return pedido.lineas.reduce((suma, linea) => suma + linea.cantidad * linea.precioUnitario, 0);\n}\n\n"
        "export function aplicarDescuento(subtotal: number, descuento: number): number {\n"
        "  return subtotal * (1 - descuento);\n}\n\n"
        "export function calcularTotal(pedido: Pedido): number {\n"
        "  const subtotal = calcularSubtotal(pedido);\n  return aplicarDescuento(subtotal, pedido.descuento);\n}\n"),
    "src/clientes.ts": "export interface Cliente { id: string; nombre: string; ciudad: string }\n\n"
                       "export function buscarCliente(clientes: Cliente[], id: string): Cliente | undefined {\n"
                       "  return clientes.find((cliente) => cliente.id === id);\n}\n",
}

TOOLS_BLOCK = """
### vps-prod
- **Type:** VPS (Ubuntu 24.04) · **Provider:** Hetzner
- **Access:** `ssh eval-tienda-vps` (alias in ~/.ssh/config) · user `deploy`
- **What runs here:** tienda-web (docker compose in `/srv/tienda`), nginx
- **Status / logs:** `docker compose -f /srv/tienda/docker-compose.yml ps` · `docker compose -f /srv/tienda/docker-compose.yml logs web --tail 200`
- **Deploy:** `cd /srv/tienda && git pull && docker compose up -d --build`
"""

FIXTURES = {"next-app": (NEXT_APP, "tienda-web"), "es-repo": (ES_REPO, "pedidos-api")}


def seed_bitacora(bt_root: Path, project: str, repo: Path, tools: bool) -> None:
    """Pre-create the project so sessions don't start in NEW PROJECT/bootstrap mode."""
    bt_root.mkdir(parents=True, exist_ok=True)
    if not (bt_root / ".git").exists():
        git(bt_root, "init", "-q")  # its own repo, no remote: the scripts' auto-commit/push stays local
        git(bt_root, "config", "user.email", "evals@localhost")
        git(bt_root, "config", "user.name", "evals")
    env = {**os.environ, "BITACORA_ROOT": str(bt_root)}
    env.pop("BITACORA_PROJECT", None)
    subprocess.run([sys.executable, str(BITACORA_PY), "--project", project, "--cwd", str(repo), "init"],
                   env=env, capture_output=True, text=True, check=True)
    pdir = bt_root / project
    summary = pdir / "SUMMARY.md"
    summary.write_text(f"# {project}\n\nEval fixture project. See the repo README.\n\n## Current state\n\n"
                       "Working MVP; no open requirements.\n", encoding="utf-8")
    if tools:
        tf = pdir / "TOOLS.md"
        text = tf.read_text(encoding="utf-8").replace("_None registered yet._", TOOLS_BLOCK.strip(), 1)
        tf.write_text(text, encoding="utf-8")
    git(bt_root, "add", "-A")
    git(bt_root, "commit", "-q", "-m", "seed", "--allow-empty")


def build(kind: str, case_dir: Path, tools: bool = False) -> tuple[Path, Path, str | None]:
    """Create the fixture for a case. Returns (workdir, bitacora_root, project)."""
    bt_root = case_dir / "bitacora"
    if kind == "empty":
        work = case_dir / "scratch"
        work.mkdir(parents=True, exist_ok=True)
        bt_root.mkdir(parents=True, exist_ok=True)
        git(bt_root, "init", "-q")
        return work, bt_root, None
    files, project = FIXTURES[kind]
    repo = case_dir / project
    _write(repo, files)
    _init_repo(repo, project)
    seed_bitacora(bt_root, project, repo, tools)
    return repo, bt_root, project
