# rubric.py — Rúbrica oficial PYCE + Descriptores CEFR B1-C2
# Todos los niveles codificados como constantes estáticas.

RUBRIC_BANDS = {
    "comunicativa": {
        "name": "Eficacia Comunicativa",
        "emoji": "🎯",
        "description": "Cumplimiento de la tarea, registro y extensión",
        "bands": {
            3: "Desarrolla eficazmente las funciones comunicativas demandadas, transmitiendo la información requerida en un texto muy claro y natural, de una extensión muy adecuada. Se adecua siempre a la situación comunicativa sin apenas inconsistencias.",
            2: "Desarrolla en general eficazmente las funciones comunicativas demandadas, transmitiendo casi toda la información requerida en un texto claro y natural, de una extensión suficientemente adecuada. Se adecua a la situación comunicativa, con alguna inconsistencia.",
            1: "Desarrolla poco eficazmente las funciones comunicativas demandadas, transmitiendo parte de la información requerida en un texto no siempre claro y natural y/o de una extensión poco adecuada. Se adecua poco a la situación comunicativa, con frecuentes inconsistencias.",
            0: "Desarrolla muy poco eficazmente las funciones comunicativas demandadas, transmitiendo muy poca información requerida en un texto poco claro y natural y/o de una extensión muy poco adecuada. Casi nunca se adecua a la situación comunicativa, o lo hace con muchas inconsistencias.",
        },
    },
    "coherencia": {
        "name": "Coherencia y Cohesión",
        "emoji": "🔗",
        "description": "Organización del discurso, conectores y progresión lógica",
        "bands": {
            3: "Estructura el discurso en párrafos y oraciones complejos y coherentes con progresión de ideas clara, lógica y fluida. Usa un amplio rango de mecanismos de cohesión textual de forma precisa y adecuada.",
            2: "Estructura el discurso en párrafos coherentes con oraciones de cierta complejidad con progresión de ideas en general clara y lógica. Usa distintos mecanismos de cohesión textual de forma generalmente precisa y adecuada.",
            1: "Estructura el discurso en párrafos y oraciones sencillos, poco coherentes, con progresión de ideas poco lógica o repetitiva. Usa un número limitado de mecanismos de cohesión textual de forma poco precisa y/o poco adecuada.",
            0: "Estructura el discurso en párrafos y/o oraciones muy sencillos, muy poco coherentes, con progresión de ideas muy poco lógica o muy repetitiva. Usa un número muy limitado de mecanismos de cohesión textual o éstos son muy sencillos.",
        },
    },
    "correccion": {
        "name": "Corrección",
        "emoji": "✏️",
        "description": "Control morfosintáctico, ortografía, puntuación e inteligibilidad",
        "bands": {
            3: "Muestra un control muy consistente de estructuras morfosintácticas, algunas más complejas y de las convenciones de ortografía y puntuación. Los muy escasos errores afectan muy poco a la inteligibilidad: queda muy claro lo que intenta decir.",
            2: "Muestra un control consistente de estructuras morfosintácticas y de las convenciones de ortografía y puntuación. Los escasos errores afectan poco a la inteligibilidad: queda generalmente claro lo que intenta decir.",
            1: "Muestra un control poco consistente de estructuras morfosintácticas y de las convenciones de ortografía y puntuación. Los frecuentes errores afectan a la inteligibilidad: queda poco claro lo que intenta decir.",
            0: "Muestra un control muy poco consistente de estructuras morfosintácticas sencillas y de las convenciones de ortografía y puntuación. Los muy frecuentes errores afectan significativamente a la inteligibilidad.",
        },
    },
    "alcance": {
        "name": "Alcance y Uso",
        "emoji": "📚",
        "description": "Variedad léxico-gramatical, exponentes funcionales, evitar repeticiones",
        "bands": {
            3: "Usa un repertorio léxico-gramatical y de exponentes funcionales amplio, variado y complejo, con escasas repeticiones. Usa un repertorio léxico de forma consistente y natural, con escasas imprecisiones.",
            2: "Usa un repertorio léxico-gramatical y de exponentes funcionales generalmente amplio y variado, con algunas repeticiones. Usa un repertorio léxico de forma generalmente consistente y natural, con pocas imprecisiones.",
            1: "Usa un repertorio léxico-gramatical y de exponentes funcionales poco amplio y variado, con frecuentes repeticiones. Usa un repertorio léxico de forma poco consistente y natural, con frecuentes imprecisiones.",
            0: "Usa un repertorio léxico-gramatical y de exponentes funcionales muy limitado y sencillo, con repeticiones muy frecuentes. Usa un repertorio léxico de forma muy poco consistente y natural.",
        },
    },
}

# CEFR level descriptors calibrating what is expected at each level
CEFR_LEVELS = {
    "B1": {
        "label": "B1 — Umbral",
        "color": "#7c3aed",
        "comunicativa": "Capable of writing simple, connected texts on familiar topics in a linear way. Struggles with formal registers; tends to mix tones (e.g. contractions in formal letters). Extension often falls short of requirements.",
        "coherencia": "Links a series of short, discrete elements into a linear sequence. Overuses basic connectors (and, but, because, then). Little clear division into conceptual paragraphs.",
        "correccion": "Sufficient control of simple, everyday structures, but commits systematic errors in complex attempts. Basic grammar/agreement errors (verb tenses, concord) may require re-reading.",
        "alcance": "Vocabulary sufficient for basic needs and familiar topics, but very flat. Relies on filler words (good, bad, things, make, get). Grammatical structures are elementary.",
        "expected_score_range": "0-1 en exámenes B2",
    },
    "B2": {
        "label": "B2 — Avanzado",
        "color": "#2563eb",
        "comunicativa": "Writes clear, detailed texts on a wide range of topics. Adapts perfectly to basic register requirements (formal letter, essay, article), though formulaic at times. Always meets length requirements.",
        "coherencia": "Text is logically and linearly structured. Separates ideas into distinct paragraphs. Uses a wide range of standard connectors accurately (However, Furthermore, In addition, On the one hand/other hand).",
        "correccion": "Good grammatical control. 'Slips' may appear in complex sentences but never impede comprehension. Spelling and punctuation control is solid throughout.",
        "alcance": "Vocabulary wide enough for clear descriptions and viewpoints without constant repetition. Attempts synonyms, phrasal verbs, collocations (take into consideration, make a decision), passive voice and complex relative clauses.",
        "expected_score_range": "2 en exámenes B2",
    },
    "C1": {
        "label": "C1 — Dominio Operativo Eficaz",
        "color": "#059669",
        "comunicativa": "Produces clear, well-structured, detailed texts on complex topics. Register adaptation is precise and sophisticated (e.g. in a Report maintains impeccable objective, persuasive distance).",
        "coherencia": "Produces a clear, highly fluent, hierarchically structured discourse. Masters complex organisational structures and advanced cohesion devices (Albeit, Consequently, Notwithstanding, In stark contrast to). Paragraph transitions are fully natural.",
        "correccion": "Maintains a consistently very high level of grammatical accuracy. Errors are extremely rare and linked exclusively to very complex experimental structures. Spelling and punctuation are impeccable.",
        "alcance": "Extensive linguistic range allowing precise nuancing without restriction. Uses advanced structures natively: Inversions (Hardly had I..., Under no circumstances...), cleft sentences (What struck me most was...), perfect modals and mixed conditionals.",
        "expected_score_range": "3 en exámenes B2",
    },
    "C2": {
        "label": "C2 — Maestría",
        "color": "#d97706",
        "comunicativa": "Writes with total fluency, naturalness and a perfectly moulded, effective style that engages the reader from the first second. Masters subtlety, irony, emphasis and complex document structures.",
        "coherencia": "Creates a completely cohesive text naturally and effortlessly. Connector and reference use is so subtle, varied and mature that their presence is invisible to the reader; ideas flow as those of a cultured native speaker.",
        "correccion": "Maintains absolute, perfect grammatical and orthotypographic control of complex language. No errors of any kind under any circumstances.",
        "alcance": "Total mastery of idioms, set phrases and sophisticated collocations. Enormous flexibility to reformulate ideas eliminating any ambiguity, using highly precise, educated and varied terms according to context.",
        "expected_score_range": "3+ en exámenes B2",
    },
}

TEXT_TYPES_B2 = {
    "formal_letter": {
        "label": "Carta / Email Formal",
        "icon": "📮",
        "requirements": [
            "Encabezado: Dear Sir/Madam o Dear Mr/Ms [Surname]",
            "Cierre: Yours faithfully (destinatario desconocido) / Yours sincerely (nombre conocido)",
            "Registro formal: sin contracciones, sin coloquialismos",
            "Propósito claro en el primer párrafo: I am writing to...",
            "Expresiones formales: I would be grateful if..., I look forward to hearing from you",
            "Párrafos estructurados: introducción, puntos del task, conclusión/call to action",
        ],
    },
    "informal_email": {
        "label": "Email / Carta Informal",
        "icon": "💬",
        "requirements": [
            "Apertura informal: Hi [Name], Hey [Name], Dear [Name]",
            "Contracciones aceptables: I'm, you're, it's, I've, don't",
            "Conectores informales: By the way, Anyway, Also, Oh, and...",
            "Cierre: Best, Take care, Love, Cheers, Bye for now",
            "Tono amigable y conversacional",
            "Todos los bullet points del task deben estar presentes",
        ],
    },
    "opinion_essay": {
        "label": "Ensayo de Opinión / For & Against",
        "icon": "💡",
        "requirements": [
            "Tesis clara en la introducción",
            "Párrafos de desarrollo: argumentos a favor Y en contra (si es for/against) o 2-3 puntos de opinión desarrollados",
            "Topic sentence al inicio de cada párrafo",
            "Conectores avanzados: Furthermore, On the other hand, Consequently, Despite this, In spite of",
            "Conclusión: reafirma la posición, NO introduce argumentos nuevos",
            "Voz neutral o personal mantenida de forma consistente",
        ],
    },
    "article": {
        "label": "Artículo / Reseña",
        "icon": "📰",
        "requirements": [
            "Título obligatorio y llamativo",
            "Hook en la primera frase para captar al lector",
            "Registro semi-formal o neutral",
            "Para reseñas: descripción + evaluación personal + recomendación",
            "Apelación directa al lector aceptable: Have you ever...? You might think...",
            "Declaración final o call to action",
        ],
    },
    "report": {
        "label": "Informe / Proposal",
        "icon": "📋",
        "requirements": [
            "Título / encabezado obligatorio",
            "Registro formal y objetivo",
            "Secciones claramente estructuradas con subtítulos",
            "Introducción que indica el propósito",
            "Secciones de hallazgos y recomendaciones",
            "Evitar pronombres personales (usar voz pasiva)",
            "Recomendaciones finales",
        ],
    },
}

SCORING_FORMULA = {
    "max_per_criterion": 3,
    "num_criteria": 4,
    "max_total": 12,
    "final_scale": 10,
    "formula": "final_score = round((sum_of_4_scores / 12) * 10, 1)",
    "pass_threshold": 5.0,
}


def get_grade_label(score: float) -> tuple:
    if score >= 9.0:
        return "Sobresaliente", "#16a34a"
    elif score >= 7.0:
        return "Notable", "#2563eb"
    elif score >= 5.0:
        return "Aprobado", "#d97706"
    else:
        return "No Apto", "#dc2626"


def calculate_final_score(scores: dict) -> float:
    total = sum(v["score"] for v in scores.values())
    return round((total / SCORING_FORMULA["max_total"]) * SCORING_FORMULA["final_scale"], 1)
