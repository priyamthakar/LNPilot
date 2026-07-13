# LNPilot v0.1 — Canonical equations

## Units (internal)

| Quantity | Canonical unit |
|----------|----------------|
| mass | µg |
| amount | nmol |
| volume | mL |
| mass concentration | mg/mL or µg/mL (context) |
| flow | mL/min |
| time | min |
| molar mass | g/mol |

## RNA phosphate (mass-based)

\[
n_P\ (\mathrm{nmol}) = \frac{m_{\mathrm{RNA}}\ (\mu\mathrm{g})\times 1000}{\overline{M}_{\mathrm{nt}}\ (\mathrm{g\,mol^{-1}})}
\]

Default \(\overline{M}_{\mathrm{nt}} = 330\ \mathrm{g\,mol^{-1}}\). **Approximate** — one phosphate per average nucleotide residue.

## N/P

\[
\frac{N}{P} = \frac{n_{\mathrm{lipid}}\times g}{n_P}
\quad\Rightarrow\quad
n_{\mathrm{lipid}} = \frac{(N/P)\,n_P}{g}
\]

where \(g\) is the **effective ionizable groups per molecule** (user-supplied).

## Composition

\[
x_i^{\mathrm{norm}} = \frac{x_i^{\mathrm{entered}}}{\sum_j x_j^{\mathrm{entered}}}
,\quad
n_i = n_{\mathrm{total}}\,x_i^{\mathrm{norm}}
,\quad
n_{\mathrm{total}} = \frac{n_{\mathrm{ionizable}}}{x_{\mathrm{ionizable}}}
\]

\[
m_i\ (\mu\mathrm{g}) = n_i\ (\mathrm{nmol})\times M_i\ (\mathrm{g\,mol^{-1}})\times 10^{-3}
\]

## Stock volume

\[
V_i\ (\mathrm{mL}) = \frac{m_i\ (\mu\mathrm{g})/1000}{c_{\mathrm{stock}}\ (\mathrm{mg\,mL^{-1}})}
\]

## Process scale

\[
m_{\mathrm{planned}} = \frac{m_{\mathrm{target}}}{R}\,(1+O)
\]

Recovery \(R > 0\), overage fraction \(O \ge 0\).

## FRR / TFR

With aqueous:organic volume ratio \(r = Q_{\mathrm{aq}}/Q_{\mathrm{org}}\):

\[
Q_{\mathrm{org}} = \frac{\mathrm{TFR}}{r+1},\quad
Q_{\mathrm{aq}} = \frac{\mathrm{TFR}\,r}{r+1}
\]

Junction organic (ethanol) volume fraction:

\[
f_{\mathrm{org}} = \frac{1}{r+1}
\]

**Not** post-dilution ethanol content.

## RiboGreen EE%

After blank correction and linear calibration invert, with dilution factors:

\[
\mathrm{EE} = \frac{c_{\mathrm{total}} - c_{\mathrm{free}}}{c_{\mathrm{total}}}
\]

only when signals are comparable, blanks/dilutions controlled, and responses in calibration range.
