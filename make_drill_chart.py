# make_drill_chart.py

import pandas as pd
from numpy import arange
from fractions import Fraction

out_file = 'drill_chart.md'

def lrange(*args):
	""" list range - can be added to other lrange """
	return list(arange(*args))

df_inch = pd.DataFrame([{'Inches (Frac)': str(Fraction(i,64))+'"', 'Inches (Dec)': i/64, 'mm': i/64*25.4, 'Source': 'Inch Fractions'} for i in lrange(1,66)+lrange(66,128,2)])
df_mm = pd.DataFrame([{'mm': mm, 'Inches (Dec)': mm/25.4, 'Source': 'mm'} for mm in lrange(0.5, 24, 0.5) + lrange(24, 50, 1)])

# this table is from https://en.wikipedia.org/wiki/Drill_bit_sizes#:~:text=Drill%20bit%20conversion%20table%5Bedit%5D
df_letter = pd.read_html("""<table class="wikitable"><tbody><tr><th>gauge</th><th>in</th><th>mm</th></tr><tr><td>A</td><td style="text-align:right;">0.234</td><td style="text-align:right;">5.944</td></tr><tr><td>B</td><td style="text-align:right;">0.238</td><td style="text-align:right;">6.045</td></tr><tr><td>C</td><td style="text-align:right;">0.242</td><td style="text-align:right;">6.147</td></tr><tr><td>D</td><td style="text-align:right;">0.246</td><td style="text-align:right;">6.248</td></tr><tr><td>E</td><td style="text-align:right;">0.250</td><td style="text-align:right;">6.350</td></tr><tr><td>F</td><td style="text-align:right;">0.257</td><td style="text-align:right;">6.528</td></tr><tr><td>G</td><td style="text-align:right;">0.261</td><td style="text-align:right;">6.629</td></tr><tr><td>H</td><td style="text-align:right;">0.266</td><td style="text-align:right;">6.756</td></tr><tr><td>I</td><td style="text-align:right;">0.272</td><td style="text-align:right;">6.909</td></tr><tr><td>J</td><td style="text-align:right;">0.277</td><td style="text-align:right;">7.036</td></tr><tr><td>K</td><td style="text-align:right;">0.281</td><td style="text-align:right;">7.137</td></tr><tr><td>L</td><td style="text-align:right;">0.290</td><td style="text-align:right;">7.366</td></tr><tr><td>M</td><td style="text-align:right;">0.295</td><td style="text-align:right;">7.493</td></tr><tr><td>N</td><td style="text-align:right;">0.302</td><td style="text-align:right;">7.671</td></tr><tr><td>O</td><td style="text-align:right;">0.316</td><td style="text-align:right;">8.026</td></tr><tr><td>P</td><td style="text-align:right;">0.323</td><td style="text-align:right;">8.204</td></tr><tr><td>Q</td><td style="text-align:right;">0.332</td><td style="text-align:right;">8.433</td></tr><tr><td>R</td><td style="text-align:right;">0.339</td><td style="text-align:right;">8.611</td></tr><tr><td>S</td><td style="text-align:right;">0.348</td><td style="text-align:right;">8.839</td></tr><tr><td>T</td><td style="text-align:right;">0.358</td><td style="text-align:right;">9.093</td></tr><tr><td>U</td><td style="text-align:right;">0.368</td><td style="text-align:right;">9.347</td></tr><tr><td>V</td><td style="text-align:right;">0.377</td><td style="text-align:right;">9.576</td></tr><tr><td>W</td><td style="text-align:right;">0.386</td><td style="text-align:right;">9.804</td></tr><tr><td>X</td><td style="text-align:right;">0.397</td><td style="text-align:right;">10.08</td></tr><tr><td>Y</td><td style="text-align:right;">0.404</td><td style="text-align:right;">10.26</td></tr><tr><td>Z</td><td style="text-align:right;">0.413</td><td style="text-align:right;">10.49</td></tr></tbody></table>""")
df_letter = df_letter[0]
df_letter = df_letter.rename(columns={'gauge': 'Inches (Frac)', 'in': 'Inches (Dec)', 'mm':'mm'})
df_letter['Source'] = 'Drill Bit Letters'

df = pd.concat([df_inch, df_letter, df_mm], ignore_index=True)
df = df.sort_values('mm', ascending=True)
df = df.fillna('')

df['mm'] = df['mm'].apply(lambda mm: f"{mm:.03f} mm")
df['Inches (Dec)'] = df['Inches (Dec)'].apply(lambda x: f'{x:.03f}"')

df.to_markdown(out_file, index=False, floatfmt=".03f", )

print(f"{len(df)} rows.")
