line_chart_template = {
    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
    "mark": {"type": "line", "point": True},
    "width": 500,
    "height": 500,
    "encoding": {
        "x": {"title": None},
        "y": {"title": None},
        "color": {"title": None},
    },
    "config": {
        "customFormatTypes": True,
        "locale": {
            "decimal": ".",
            "thousands": ",",
            "grouping": [3, 2, 2, 2, 2, 2, 2, 2, 2, 2],
            "currency": ["₹", ""],
        },
        "axis": {
            "labelPadding": 10,
            "domain": False,
            "title": None,
            "grid": True,
            "gridDash": [3, 3],
            "ticks": False,
            "labelFont": "Inter",
            "titleFont": "Inter",
        },
        "axisX": {"labelAngle": -45},
        "axisY": {
            "tickCount": 6,
        },
        "legend": {
            "orient": "bottom",
            "title": None,
            "columnPadding": 10,
            "labelFont": "Inter",
            "titleFont": "Inter",
        },
        "view": {"stroke": "transparent"},
    },
}


bar_chart_template = {
    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
    "description": "Base Bar Chart Configuration",
    "mark": "bar",
    "encoding": {
        "x": {
            "field": "Category",
            "type": "ordinal",
            "axis": {
                "title": None,
                "labelAngle": -45,
                "grid": True
            }
        },
        "y": {
            "field": "Value",
            "type": "quantitative",
            "axis": {
                "title": None,
                "grid": True,
                "format": "~s",
                "formatType": "number",
                "labels": True,
                "labelExpr": "datum.value >= 10000000 ? (datum.value / 10000000) + ' Cr' : datum.value >= 100000 ? (datum.value / 100000) + ' L' : datum.value"
            }
        },
        "tooltip": [
            {"field": "Category", "type": "ordinal"},
            {"field": "Value", "type": "quantitative", "format": ",.0f"}
        ],
        "color": {
            "field": "Category",
            "type": "nominal",
            "legend": {
                "orient": "bottom",
                "title": None,
                "labelFontSize": 12
            }
        }
    },
    "config": {
        "axis": {
            "labelFontSize": 12,
            "titleFontSize": 14
        },
        "legend": {
            "orient": "bottom",
            "title": None,
            "labelFontSize": 12
        },
        "view": {
            "stroke": "transparent"
        }
    }
}

pie_chart_template = {
    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
    "description": "Base Pie Chart Configuration",
    "mark": "arc",
    "encoding": {
        "theta": {
            "field": "Value",
            "type": "quantitative"
        },
        "color": {
            "field": "Category",
            "type": "nominal",
            "legend": {
                "orient": "bottom",
                "title": None,
                "labelFontSize": 12
            }
        },
        "tooltip": [
            {"field": "Category", "type": "nominal"},
            {"field": "Value", "type": "quantitative", "format": ",.0f"}
        ]
    },
    "view": {
        "stroke": "transparent"
    },
    "config": {
        "legend": {
            "orient": "bottom",
            "title": None,
            "labelFontSize": 12
        }
    }
}
