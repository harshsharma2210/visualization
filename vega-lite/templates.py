

line_chart_template =  {
    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
    "data": {},
    "mark": {
        "type": "line",
        "point": True
    },
    "config": {
        "customFormatTypes": True,
        "locale": {
            "decimal": ".",
            "thousands": ",",
            "grouping": [3, 2],
            "currency": ["₹", ""]
        },
        "axis": {
            "title": None,
            "grid": True,
            "labelFont": "Arial",
            "labelFontSize": 12,
            "gridColor": "#ccc",
            "gridOpacity": 0.5
        },
        "axisX": {
            "labelAngle": -45
        },
        "axisY": {},
        "legend": {
            "orient": "bottom",
            "title": None,
            "labelFont": "Arial",
            "labelFontSize": 12
        },
        "view": {
            "stroke": "transparent"
        }
    }
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
