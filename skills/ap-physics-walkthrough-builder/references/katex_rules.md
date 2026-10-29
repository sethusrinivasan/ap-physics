# KaTeX Formatting Rules for Interactive Walkthroughs

KaTeX is used for fast, crisp client-side math rendering in the interactive player. All math expressions must follow these conventions:

---

## 1. Display Modes

* **Block Formulas**: Fenced within display math blocks `\\[ ... \\]`.
* **Inline Formulas**: Enclosed within single delimiters `\\( ... \\)`.
* **Player Configuration**: Left-aligned equations are enforced via `{ fleqn: true }` in KaTeX auto-render options.

---

## 2. Common Patterns & Best Practices

| Physics Concept | Recommended KaTeX Syntax | Avoid |
| :--- | :--- | :--- |
| **Fractions** | `\dfrac{a}{b}` (larger, clearer in display) | `a / b` in display math |
| **Square Roots** | `\sqrt{2mK}` | `(2mK)^{1/2}` |
| **Vectors** | `\vec{v}`, `\vec{p}`, `\vec{F}_{\text{net}}` | Boldface `\mathbf{v}` |
| **Subscripts** | `v_{1f}`, `p_{\text{tot}}`, `v_{\text{cm}}` | `v1f`, `v_cm` (without braces) |
| **Derivatives** | `\dfrac{dx}{dt}`, `\dfrac{dp}{dt}` | `dx/dt` |
| **Integrals** | `\int_{t_1}^{t_2} F(t) \, dt` | `\int F dt` (missing spacing `\,`) |
| **Units** | `5.0\,\text{m/s}`, `2.5\,\text{kg}\cdot\text{m/s}` | `5.0 m/s` (unformatted italics) |
| **Proportionality** | `v \propto \dfrac{1}{m}` | `v ~ 1/m` |

---

## 3. Escaping & String Safety

* In Python files generating HTML or JSON:
  * Always use raw string literals (`r"..."`) or double-escape backslashes (`\\dfrac`, `\\sqrt`).
  * In JSON structures: ensure backslashes are valid JSON escapes (`\\dfrac`).
