from typing import Union

from neuralogic.core.constructs.metadata import Metadata
from neuralogic.core.enums import Activation
from neuralogic.core.constructs.factories import R, V
from neuralogic.nn.module.module import Module


class RNNCell(Module):
    r"""

    Parameters
    ----------

    input_size : int
        Input feature size.
    hidden_size : int
        Output and hidden feature size.
    output_name : str
        Output (head) predicate name of the module.
    input_name : str
        Input feature predicate name to get features from.
    hidden_input_name : str
        Predicate name to get hidden state from.
    activation : Activation
        Activation function.
        Default: ``Activation.TANH``
    arity : int
        Arity of the input and output predicate. Default: ``1``
    input_time_step : bool
        Include the time/iteration step as extra (last) term in the input predicate.
        Default: ``True``
    next_name : str
        Predicate name to get positive integer sequence from.
        Default: ``_next__positive``
    """

    def __init__(
        self,
        input_size: int,
        hidden_size: int,
        output_name: str,
        input_name: str,
        hidden_input_name: str,
        activation: Activation = Activation.TANH,
        arity: int = 1,
        input_time_step: bool = True,
        next_name: str = "_next__positive",
    ):
        self.input_size = input_size
        self.hidden_size = hidden_size

        self.output_name = output_name
        self.input_name = input_name
        self.hidden_input_name = hidden_input_name

        self.activation = activation
        self.arity = arity
        self.next_name = next_name
        self.input_time_step = input_time_step

    def __call__(self):
        terms = [f"X{i}" for i in range(self.arity)]
        output = R.get(self.output_name)

        input_terms = terms
        if self.input_time_step:
            input_terms = [*input_terms, V.Y]

        rnn_rule = output([*terms, V.Y]) <= (
            R.get(self.input_name)(input_terms)[self.hidden_size, self.input_size],
            R.get(self.hidden_input_name)([*terms, V.Z])[self.hidden_size, self.hidden_size],
            R.get(self.next_name)(V.Z, V.Y),
        )

        return [
            rnn_rule | [Activation.IDENTITY],
            output / (self.arity + 1) | Metadata(activation=self.activation),
        ]


class RNN(Module):
    r"""

    Parameters
    ----------

    input_size : int
        Input feature size.
    hidden_size : int
        Output and hidden feature size.
    num_layers : int
        Number of hidden layers.
    output_name : str
        Output (head) predicate name of the module.
    input_name : str
        Input feature predicate name to get features from.
    hidden_0_name : str
        Predicate name to get initial hidden state from.
    activation : Activation
        Activation function.
        Default: ``Activation.TANH``
    arity : int
        Arity of the input and output predicate. Default: ``1``
    input_time_step : bool
        Include the time/iteration step as extra (last) term in the input predicate.
        Default: ``True``
    next_name : str
        Predicate name to get positive integer sequence from.
        Default: ``_next__positive``
    """

    def __init__(
        self,
        input_size: int,
        hidden_size: int,
        num_layers: int,
        output_name: str,
        input_name: str,
        hidden_0_name: str,
        activation: Activation = Activation.TANH,
        arity: int = 1,
        input_time_step: bool = True,
        next_name: str = "_next__positive",
    ):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers

        self.output_name = output_name
        self.input_name = input_name
        self.hidden_0_name = hidden_0_name

        self.activation = activation
        self.arity = arity
        self.next_name = next_name
        self.input_time_step = input_time_step

    def __call__(self):
        temp_output_name = f"{self.output_name}__rnn_cell"

        recursive_cell = RNNCell(
            self.input_size,
            self.hidden_size,
            temp_output_name,
            self.input_name,
            temp_output_name,
            self.activation,
            self.arity,
            self.input_time_step,
            self.next_name,
        )

        next_relation = R.get(self.next_name)
        terms = [f"X{i}" for i in range(self.arity)]

        output_relation = R.get(self.output_name)

        return [
            *[next_relation(i, i + 1) for i in range(0, self.num_layers)],
            (R.get(temp_output_name)([*terms, 0]) <= R.get(self.hidden_0_name)(terms)) | [Activation.IDENTITY],
            *recursive_cell(),
            (output_relation(terms) <= R.get(temp_output_name)([*terms, self.num_layers])) | [Activation.IDENTITY],
            output_relation / self.arity | [Activation.IDENTITY],
        ]
