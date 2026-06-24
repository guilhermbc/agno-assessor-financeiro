import reflex as rx

config = rx.Config(
    app_name="agno_assessor_financeiro",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ]
)