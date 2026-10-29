# Text-to-Speech (TTS) Pronunciation Rules

Natural-sounding speech narration is essential for an effective audio walkthrough. Because TTS engines pronounce raw math formulas awkwardly, every mathematical equation has a dedicated `"speakFormula"` or `"say"` string formatted in phonetic English.

---

## 1. Symbol Pronunciation Dictionary

| Symbol / TeX | `"say"` English Pronunciation | Avoid |
| :--- | :--- | :--- |
| `v_x` | `"v x"` | `"v sub x"` |
| `v_y` | `"v y"` | `"v sub y"` |
| `p_0` | `"p zero"` | `"p naught"` or `"p sub zero"` |
| `K_0` | `"K zero"` | `"K naught"` |
| `m_1, m_2` | `"m 1 and m 2"` | `"m sub 1 and m sub 2"` |
| `\Delta p` | `"delta p"` | `"triangle p"` |
| `|\Delta p|` | `"magnitude of delta p"` | `"absolute value of delta p"` |
| `v_{\text{cm}}` | `"v c m"` | `"v com"` |
| `v_{\text{rel}}` | `"v relative"` | `"v rel"` |
| `\theta` | `"theta"` | `"zero with line"` |
| `\int_0^t F \, dt` | `"integral from zero to t of F d t"` | `"int zero t"` |
| `\dfrac{dx}{dt}` | `"d x d t"` or `"derivative of x with respect to t"` | `"dx over dt"` |
| `\sqrt{x}` | `"square root of x"` | `"radical x"` |
| `\hat i` | `"i hat"` | `"i caret"` |
| `x^2` | `"x squared"` | `"x power 2"` |
| `t^3` | `"t cubed"` | `"t power 3"` |

---

## 2. Audio Pacing & Sentence Structure

1. **Short Sentences**: Split complex reasoning into short, punchy sentences under 140 characters.
2. **Punctuation**: Use commas and periods to enforce natural pauses between mathematical concepts.
3. **Number Pronunciation**:
   * `"0.50"` $\to$ Write as `"0.50"` or `"zero point five zero"`.
   * `"2.5 kg*m/s"` $\to$ Write as `"2.5 kilogram meters per second"`.
   * `"10 N*s"` $\to$ Write as `"10 newton seconds"`.
