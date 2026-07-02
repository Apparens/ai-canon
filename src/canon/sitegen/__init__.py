"""Stage C site generator, split into small modules.

common: paths, constants, escaping, load/write helpers
theme:  the stylesheet, JSON-LD, CSP hash, Cloudflare _headers
shell:  nav, share row, and the page shell every page renders through
pages_*: the page renderers (corpus / context / meta shelves)
assets_js: the external JS bundles and the search-index builder

canon.export_site remains the orchestrator and the public import surface.
"""
