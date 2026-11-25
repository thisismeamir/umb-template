Universal Metadata Browser (UMB) Documentation
==============================================

The **Universal Metadata Browser (UMB)** is a modular, domain-driven metadata catalog platform built for structured scientific and HEP/FCC physics datasets. It combines a PostgreSQL JSONB + ``pg_trgm`` storage layer, an ANTLR4-compiled JSON Request DSL, a Redis-backed durable async worker queue, and a Nuxt 3 web interface.

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   user-guide/quickstart
   user-guide/request-dsl
   user-guide/search-analytics-export

.. toctree::
   :maxdepth: 2
   :caption: Third-Party Usage Guide

   third-party/overview
   third-party/api-reference
   third-party/python-integration
   third-party/cli-and-curl
   third-party/custom-ingestion

.. toctree::
   :maxdepth: 2
   :caption: Developer Guide

   developer-guide/architecture
   developer-guide/local-dev-and-testing
   developer-guide/extending-umb

.. toctree::
   :maxdepth: 2
   :caption: Operations & Deployment

   operations/configuration-and-deployment
