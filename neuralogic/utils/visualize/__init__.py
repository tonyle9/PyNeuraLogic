import os
import tempfile
from typing import Optional

import jpype

from neuralogic.core.settings import Settings, SettingsProxy


def get_drawing_settings(
    img_type: str = "png", value_detail: int = 0, graphviz_path: Optional[str] = None
) -> SettingsProxy:
    """Returns the default settings instance for drawing with a specified image type.

    :param img_type:
    :param value_detail:
    :param graphviz_path:
    :return:
    """
    settings = Settings().create_proxy()

    if graphviz_path is not None:
        settings.settings.graphvizPath = graphviz_path

    settings.settings.drawing = False
    settings.settings.storeNotShow = True
    settings.settings.imgType = img_type.lower()
    settings.settings.outDir = tempfile.gettempdir()

    if value_detail not in [0, 1, 2]:
        raise NotImplementedError

    settings_class = settings.settings_class
    details = [
        settings_class.shortNumberFormat,
        settings_class.detailedNumberFormat,
        settings_class.superDetailedNumberFormat,
    ]

    settings.settings.defaultNumberFormat = details[value_detail]

    return settings


def get_template_drawer(settings: SettingsProxy):
    return jpype.JClass("cz.cvut.fel.ida.pipelines.debugging.drawing.TemplateDrawer")(settings.settings)


def get_sample_drawer(settings: SettingsProxy):
    return jpype.JClass("cz.cvut.fel.ida.pipelines.debugging.drawing.NeuralNetDrawer")(settings.settings)


# todo gusta: + groundingDrawer, pipelineDrawer...


def draw(drawer, obj, filename: Optional[str] = None, draw_ipython=True, img_type="png", *args, **kwargs):
    if filename is not None:
        try:
            drawer.drawIntoFile(obj, os.path.abspath(filename))
        except jpype.java.lang.NullPointerException as e:
            raise Exception(
                "Drawing raised NullPointerException. Try to install GraphViz (https://graphviz.org/download/) on "
                "your Path or specify the path via the `graphviz_path` parameter"
            ) from e

        return

    data = drawer.drawIntoBytes(obj)

    if data is None:
        raise Exception(
            "Drawing failed. Try to install GraphViz (https://graphviz.org/download/) on your Path or specify the "
            "path via the `graphviz_path` parameter"
        )

    data = bytes(data)

    if draw_ipython:
        from IPython.display import Image, SVG

        if img_type.lower() == "svg":
            return SVG(data, *args, **kwargs)
        return Image(data, *args, **kwargs)
    return data


def to_dot_source(drawer, obj) -> str:
    return str(drawer.getGraphSource(obj))


def draw_model(
    model,
    filename: Optional[str] = None,
    draw_ipython=True,
    img_type="png",
    value_detail: int = 0,
    graphviz_path: Optional[str] = None,
    *args,
    **kwargs,
):
    """Draws model either as an image of type img_type either into:
        * a file - if filename is specified),
        * an IPython Image - if draw_ipython is True
        * or bytes otherwise

    :param model:
    :param filename:
    :param draw_ipython:
    :param img_type:
    :param value_detail:
    :param graphviz_path:
    :param args:
    :param kwargs:
    :return:
    """
    if model.need_sync:
        model.sync_template()

    template = model.template
    template_drawer = get_template_drawer(get_drawing_settings(img_type, value_detail, graphviz_path))

    return draw(template_drawer, template, filename, draw_ipython, img_type, *args, **kwargs)


def draw_sample(
    sample,
    filename: Optional[str] = None,
    draw_ipython=True,
    img_type="png",
    value_detail: int = 0,
    graphviz_path: Optional[str] = None,
    *args,
    **kwargs,
):
    """Draws sample either as an image of type img_type either into:
        * a file - if filename is specified),
        * an IPython Image - if draw_ipython is True
        * or bytes otherwise

    :param sample:
    :param filename:
    :param draw_ipython:
    :param img_type:
    :param detail:
    :param graphviz_path:
    :param args:
    :param kwargs:
    :return:
    """
    draw_object = sample.java_sample

    sample_drawer = get_sample_drawer(get_drawing_settings(img_type, value_detail, graphviz_path))

    return draw(sample_drawer, draw_object, filename, draw_ipython, img_type, *args, **kwargs)


def model_to_dot_source(model) -> str:
    """Renders the model into its dot source representation.

    :param model:
    :return:
    """
    if model.need_sync:
        model.sync_template()

    template = model.template
    template_drawer = get_template_drawer(get_drawing_settings())

    return to_dot_source(template_drawer, template)


def sample_to_dot_source(sample, value_detail: int = 0) -> str:
    """Renders the sample into its dot source representation.

    :param sample:
    :param value_detail:
    :return:
    """
    sample_drawer = get_sample_drawer(get_drawing_settings(value_detail=value_detail))

    return to_dot_source(sample_drawer, sample.java_sample)
