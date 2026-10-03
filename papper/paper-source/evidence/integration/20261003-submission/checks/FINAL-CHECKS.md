# Final technical checks — 3 October 2026

This is an agent technical review, not external peer review, scientific acceptance,
or author approval. The original dirty Desktop checkout was not edited. Work took
place in an isolated clone on `codex/vadimnbkg/92-monotec-submission`, integration #92.

## Manuscript and evidence

- H, F and S remain separate identities. Numerical assertions were checked against
  archived run records and a separate agent's source review.
- The agent review found and the revision corrected transport-clock ownership,
  two APP placeholders, the meaning of the historical end-of-ACK-wait query, and
  unsupported wording about reachable-state growth.
- All 32 selected figure transitions and their full catalogue were checked against
  the unchanged S XML. Five explanatory glosses were corrected. Omitted edges are listed.
- Reviewer response references match Sections 1–10, Figures 1–4, Tables 1–6,
  Equations 1–7 and nine bibliography entries. Scientific partial/open items remain explicit.
- #89's checkpoint failed the truthful-identity precondition before execution.
  No Hnom materialization, execution lease, verifier attempt or slot consumption occurred.
  Original controls were inspected, not rerun. See protocol-review.md and #89 comment.

## PDF and figures

- Built with TeX Live 2023/Debian, latexmk 4.83, Springer llncs 2.24 and BibTeX.
- 15 pages; no undefined references/citations and no overfull boxes in the final log.
- The class/amsmath `Unable to redefine math accent vec` warning is retained; the
  manuscript does not use that accent. Benign underfull spacing warnings are not hidden.
- All used PDF fonts are embedded; see pdf-fonts.txt. Figure text is 7.5–8 pt at
  the 122 mm publication width. All 15 pages were visually inspected, with additional
  full-page checks of figures, equations, tables and bibliography after fixes.
- Figures 1–4 are within their respective sections on PDF pages 5, 6, 7 and 9.
  The article uses legible XML-derived transition panels, not claimed native screenshots.
- A complete native APP EPS export was obtained through the existing UPPAAL UI
  from sources/layout-model.xml and losslessly gzip-compressed. Its XML copy was
  not edited; source and copy have the same S hash. This supplementary full view is
  not used as the compact article illustration.

## Word and reviewer response

- DOCX was generated from the same TeX revision, resolving citations/references
  from the final AUX and importing the exact BBL bibliography.
- Six editable tables, four images, 42 Office Math nodes including seven display
  equations, numbered figure/table captions and nine numbered references.
- Initial render exposed mixed-interval delimiter errors, missing caption/reference
  numbers, an align-array artifact and an oversized-image layout. These were fixed
  through Pandoc's OMML conversion and document styling, then rerendered and checked.
- The final DOCX renders to 16 pages in LibreOffice. All pages were inspected; the
  last table fits on one page. Text alternatives accompany figures and are embedded
  in DOCX image descriptions. Main PDF remains the 15-page TeX rendering.
- The six-page reviewer response was created from one Markdown source and rendered
  through LibreOffice; its PDF and DOCX have matching content and were inspected.
- Computer Use attempted to launch Microsoft Word, but system app approval timed
  out. Native Word UI inspection did not occur; no alternative UI control bypass
  was used. LibreOffice's actual document rendering supplies the visual check.
- The first skill-renderer run produced pages but returned a Windows temporary
  updater-lock cleanup error. The final wrapper permits only temporary cleanup
  failures; subsequent conversion and rasterization completed successfully.

## Reproduction and remaining boundaries

Structured artifact checks, file hashes and final archive identities are recorded
separately. The source ZIP preserves selected original evidence, including the
unexecuted #89 protocol pinned to its distinct checkpoint. The full Git bundle
preserves the integration branch history; it is not a conference submission.

No new scientific verifier campaign, software-wide test suite, scientific gate
acceptance, merge, signature, conference submission or ITMO clearance was performed.
The unresolved scientific properties cannot be closed by document formatting.
