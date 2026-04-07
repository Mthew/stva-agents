# Datos Operacionales — Instrucciones

Esta carpeta contiene los datos financieros de Sativa Liquor que el CFO Agent usa para generar reportes.
**Entrada manual** hasta que haya integración con sistemas externos (Fase 4).

---

## sales/sales.csv — Registro de ventas

Añadir una fila por cada venta o al final de cada día con el resumen.

**Columnas:**
```
fecha,producto,cantidad,precio_unitario,total,canal,notas
```

| Campo | Formato | Ejemplo |
|---|---|---|
| `fecha` | YYYY-MM-DD | `2026-04-06` |
| `producto` | Nombre del producto | `Granizado Sativa`, `Promo 2x` |
| `cantidad` | Número entero | `12` |
| `precio_unitario` | Número entero (COP) | `13000` |
| `total` | Número entero (COP) | `156000` |
| `canal` | `presencial` o `domicilio` | `presencial` |
| `notas` | Texto libre opcional | `Sábado, DJ invitado` |

---

## expenses/expenses.csv — Registro de gastos

Añadir una fila por cada gasto.

**Columnas:**
```
fecha,categoria,descripcion,monto,notas
```

| Campo | Formato | Ejemplo |
|---|---|---|
| `fecha` | YYYY-MM-DD | `2026-04-06` |
| `categoria` | `insumos`, `publicidad`, `infraestructura`, `nomina`, `otros` | `insumos` |
| `descripcion` | Texto libre | `Compra de licor semana 14` |
| `monto` | Número entero (COP) | `85000` |
| `notas` | Texto libre opcional | |
