# eurohook-3D

Modèles 3D d'étiquetage filaire pour le retail : **euro hook** (aussi appelé *pegboard hook* ou *crochet pour panneau perforé*).

Le modèle livré est un euro hook « looped » classique, en fil d'acier :

| Paramètre | Valeur |
|---|---|
| Diamètre du fil | 4,0 mm |
| Bras de présentoir | 2 bras parallèles horizontaux, 200 mm hors panneau |
| Entraxe des deux brins | 25,4 mm (trame perforée *pegboard* 1 pouce) |
| Boucle arrière | 180° derrière le panneau (pont fixe), rayon 12,7 mm |
| Pointes anti-glisse | recourbées vers le haut, 130° / R10 mm |

## Fichiers

- **`euro_hook_200mm.obj`** — le modèle 3D (Wavefront OBJ), généré automatiquement à chaque mise à jour du script par le workflow GitHub Actions.
- `generate_euro_hook.py` — script paramétrique qui produit le `.obj`.
- `preview_centerline.svg` — aperçu de la ligne médiane (vue de côté et de dessus).

## Caractéristiques du maillage

- Unités : **1 unité = 1 mm**. Panneau = plan `x = 0`, bras vers `+x`, `+z` vertical.
- Maillage de quads lissés (tube balayé le long de la ligne médiane) avec normales par sommet et bouchons plats.
- **Étanche (watertight)**, enroulement des faces sortant, volume ≈ 7,2 cm³ — utilisable pour le rendu, l'impression 3D ou la CAO.

## Générer le `.obj` soi-même

```bash
pip install numpy
python generate_euro_hook.py
```

Le fichier `euro_hook_200mm.obj` est écrit dans le dossier courant.

## Décliner d'autres dimensions

Modifiez les constantes en tête de `generate_euro_hook.py` puis relancez-le :

- `WIRE_DIA` : diamètre du fil (5 ou 6 mm pour les charges lourdes)
- `ARM_LEN` : longueur des bras (100–300 mm)
- `PRONG_SPACING` : entraxe des brins
- `TIP_ANGLE` / `TIP_R` : recourbement des pointes
- `RADIAL_SEGMENTS`, `STRAIGHT_STEP`, `ARC_STEP_DEG` : finesse du maillage
