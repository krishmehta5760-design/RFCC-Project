# What is in 04_Results (and what matters)

Everything here was produced by the openEMS scripts in `03_openEMS_Simulation`.
You only need the **starred** files for the presentation. The rest are backup or evidence.

**Shortcut:** `00_IMPORTANT_PLOTS/` holds copies of the 5 key plots, renamed and numbered in presentation order.

## plots/ (pictures)

### ⭐ The 5 that matter (know these)
| File | What it shows | One sentence to say |
|---|---|---|
| `post3_cheby.png` | The paper's main filter (3rd-order, posts, Chebyshev), simulated by us | "At the band edge (10.25 GHz) reflection rises to −5.8 dB, so this design does not meet the 20 dB spec." |
| `iris3_cheby.png` | The paper's iris version of the same filter | "This is our closest match to the paper; it is also the one we run live in the demo." |
| `post_K_phi_extraction.png` | Measured coupling of one post vs its diameter | "This is the diagnosis: the paper's posts give the wrong coupling, so they are the wrong size." |
| `improved_vs_paper.png` | Paper design (black dashed) vs our improved 3rd- and 4th-order designs | "Our 4th-order design keeps reflection below −20 dB across the whole 9.75–10.25 GHz band." |
| `full_board_comparison.png` | The complete 96.4 × 20 mm board with microstrip connectors | "On the real board the improved filter still works: 17.7 dB return loss, 0.74 dB loss." |

### Pictures of the structures (show if asked "what did you simulate?")
| File | What it is |
|---|---|
| `geom_post3_cheby.png` | Top view of the paper's post filter |
| `geom_iris3_cheby.png` | Top view of the paper's iris filter |
| `geom_iris3_vias.png` | Iris filter built from small vias instead of solid walls |
| `geom_improved_post3.png`, `geom_improved_post4.png` | Our improved 3rd- and 4th-order filters |
| `geom_full_board_paper.png`, `geom_full_board_improved.png` | Complete boards with tapers and microstrip lines |

### Backup / extra evidence
| File | What it is |
|---|---|
| `Fig8a_3rd_butterworth.png`, `Fig8b_3rd_chebyshev.png`, `Fig9_5th_chebyshev.png`, `Fig11_iris_walls_vs_vias.png` | Our versions of the paper's Figures 8a, 8b, 9 and 11, to compare side by side with the paper |
| `post3_butter.png`, `iris3_butter.png`, `post5_cheby.png`, `iris5_cheby.png`, `iris3_cheby_vias.png` | One plot per remaining paper design (7 designs in total), with the paper's numbers as square markers |
| `improved_vs_paper_IL_zoom.png` | Zoom on the loss (top 3 dB) inside the pass band |
| `siw_line.png` | Empty SIW guide with no filter: a sanity check that the model passes everything above the 6.56 GHz cut-off with almost no loss |
| `transition_sweep.png` | Choosing the taper width of the microstrip-to-SIW transition (7.5 mm was best) |

## tables/ (numbers)
| File | What it is |
|---|---|
| ⭐ `validation_table.md` | **The one to open.** Paper vs openEMS at 9.75, 10.00 and 10.25 GHz for every design (open it in Notepad or VS Code) |
| `validation_table.json` | The same table in machine-readable form |
| `metrics_<design>.json` | One file per paper design: centre frequency, bandwidth, loss, return loss, rejection |
| `post_K_extraction.json` | The numbers behind `post_K_phi_extraction.png` |
| `improved_design.json` | Post sizes and spacings of the improved designs, and their results |
| `mesh_convergence.json` | Same filter at normal and fine mesh: results barely change, so the mesh is fine enough |
| `full_board_results.json` | Numbers behind `full_board_comparison.png` and `transition_sweep.png` |

## touchstone/ (.s2p files)
`.s2p` (Touchstone) is the standard file format for S-parameters. Any RF tool (ADS, AWR, CST, MATLAB, Python scikit-rf) can open them.
You do not need to open them. If asked, say: *"We also exported every result as industry-standard Touchstone files, so they can be loaded into other RF tools."*

| File | Design |
|---|---|
| `post3_*`, `iris3_*`, `post5_*`, `iris5_*`, `iris3_cheby_vias` | The 7 paper designs |
| `improved_n4r003.s2p` | ⭐ **Final improved design**: 4th order, 0.03 dB ripple |
| `improved_n3r003.s2p`, `improved_n3r002.s2p` | Improved 3rd-order variants (0.03 dB and 0.02 dB ripple) |
| `board_paper_post3.s2p`, `board_improved_post3.s2p` | Complete boards with microstrip ports. Despite its name, the "improved" board holds the **final 4th-order** filter |
| `transition_back_to_back.s2p` | Two microstrip-to-SIW transitions with no filter |
| `improved_post3.s2p` | Old leftover from an earlier run; ignore it |

## Name decoder
- `post` = filter made with metal posts (vias) inside the guide; `iris` = filter made with metal walls (windows)
- `3`, `5` = filter order (number of resonators)
- `butter` = Butterworth (flat, no ripple); `cheby` = Chebyshev (small ripple, sharper edges)
- `n4r003` = order **4**, ripple **0.03** dB
