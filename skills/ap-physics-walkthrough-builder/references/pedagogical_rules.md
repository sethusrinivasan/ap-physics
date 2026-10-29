# Pedagogical Standards for Walkthrough Steps

Every walkthrough follows a strict 7-step pedagogical architecture designed for clarity, rigor, and cognitive accessibility.

---

## The 7-Step Model

### Step 1: Look at the setup
* **Purpose**: Establish physical context before jumping into formulas.
* **Requirements**:
  * Name the physical system (e.g., "cart on a frictionless track", "block sliding on a ramp").
  * Identify given variables with their units ($m = 0.5\,\text{kg}$, $v = 4.0\,\text{m/s}$).
  * State what is held constant versus what changes.
  * Every symbol must be defined in plain English before appearing in the formula list.

### Step 2: Name what the question asks
* **Purpose**: Keep the student oriented on the exact target.
* **Requirements**:
  * Name the single target quantity (e.g., "magnitude of linear momentum", "ratio of energy lost").
  * Assign the target variable ($p$, $v_f$, $\Delta K_2 / \Delta K_1$).
  * Prevent students from getting distracted by extraneous details in the figure.

### Step 3: Use the governing idea
* **Purpose**: Introduce the fundamental physical law.
* **Requirements**:
  * State the law in plain English first (e.g., "linear momentum is conserved in the absence of net external forces").
  * Write the governing equation in KaTeX math (e.g., `p = \sqrt{2mK}`).
  * Pronounce the equation naturally in the speech field (e.g., "p equals the square root of 2 m K").

### Step 4: Substitute the given values
* **Purpose**: Bridge general theory to the specific problem parameters.
* **Requirements**:
  * Plug in the numbers or specific variable expressions from the question.
  * Clearly show unit conversions or vector coordinate decompositions.
  * Explain intermediate simplifications step-by-step.

### Step 5: Carry the argument through
* **Purpose**: Complete the algebraic or arithmetic solution.
* **Requirements**:
  * Simplify directly to the final form or numerical value.
  * Explicitly compare the result with the target expression in the correct multiple-choice letter.

### Step 6: Why the other choices fail
* **Purpose**: Strengthen conceptual understanding and prevent common pitfalls.
* **Requirements**:
  * Address the incorrect answer options (e.g., "Choices A, C, and D fail because...").
  * Pinpoint the exact physical or arithmetic mistake each wrong choice represents (e.g., subtracting speeds instead of adding during a rebound, forgetting to square, or dropping mass factors).

### Step 7: The answer is X
* **Purpose**: Affirm the correct selection with official scoring alignment.
* **Requirements**:
  * State the correct letter (A, B, C, or D) prominently.
  * Reiterate the single-sentence rationale matching the official College Board scoring key.
  * Mark with `"highlight": True` so the player accents the final answer.

---

## Variable and Formatting Conventions

1. **Subscripts**:
   * Use lowercase for generic labels: $v_x, v_y, p_i, p_f, v_{\text{cm}}, v_{\text{rel}}$.
   * Use uppercase or numbers only when printed directly in the exam: $m_0, 2m_0, K_0, p_0, m_1, m_2, F_T, v_{\text{Pcm}}$.
2. **Vectors**:
   * Use `\vec{v}` and `\vec{p}` when discussing vector direction.
   * Use scalar notation ($v$, $p$) when calculating magnitude.
3. **Symbols before Formulas**:
   * Never introduce an unexplained symbol in an equation block without defining it first in the `"vars"` list.
