import matplotlib.pyplot as plt

periodos = ['1° Semestre 2023', '1° Semestre 2024']
ventas = [550, 225]

fig, ax = plt.subplots(figsize=(6, 5))
bars = ax.bar(periodos, ventas, color=['#2ca02c', '#d62728'], width=0.5)

# Añadir etiquetas de valor
for bar in bars:
    yval = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2, yval + 10, f"US$ {yval}M", ha='center', va='bottom', fontweight='bold', fontsize=11)

ax.set_ylabel('Ventas (Millones de US$)')
ax.set_title('Ventas de Celulares y Notebooks en Argentina', fontweight='bold')
ax.set_ylim(0, 650)
ax.grid(axis='y', linestyle='--', alpha=0.7)

plt.tight_layout()
plt.show()