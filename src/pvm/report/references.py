"""Report section: references."""
from __future__ import annotations

import datetime

from docx.shared import Pt

from ..docs_common import (DS_NAME, DS_SHORT, METHOD_NAME, ci, eps_str, fmt_bytes, num, pm)
from .helpers import AUTHOR, TITLE, accuracy_rows, verdict


def add(doc, ctx):
    S, D, syn, eic, H, P = ctx.S, ctx.D, ctx.syn, ctx.eic, ctx.H, ctx.P
    doc.h("References", 1)
    for r in [
        "McMahan, H. B., Moore, E., Ramage, D., Hampson, S., Agüera y Arcas, B. (2017). Communication-Efficient Learning of Deep Networks from Decentralized Data. AISTATS.",
        "Abadi, M., Chu, A., Goodfellow, I., McMahan, H. B., Mironov, I., Talwar, K., Zhang, L. (2016). Deep Learning with Differential Privacy. ACM CCS.",
        "Mironov, I. (2017). Rényi Differential Privacy. IEEE Computer Security Foundations Symposium.",
        "Armbrust, M., Das, T., Torres, J., Yavuz, B., Zhu, S., Xin, R., Ghodsi, A., Stoica, I., Zaharia, M. (2018). Structured Streaming: A Declarative API for Real-Time Applications in Apache Spark. ACM SIGMOD.",
        "Kreps, J., Narkhede, N., Rao, J. (2011). Kafka: a Distributed Messaging System for Log Processing. NetDB Workshop.",
        "Pollard, T. J., Johnson, A. E. W., Raffa, J. D., Celi, L. A., Mark, R. G., Badawi, O. (2018). The eICU Collaborative Research Database, a freely available multi-center database for critical care research. Scientific Data 5, 180178.",
    ]:
        para = doc.d.add_paragraph(r, style="List Number")
        para.paragraph_format.space_after = Pt(2)
        for run in para.runs:
            run.font.size = Pt(9.5)
