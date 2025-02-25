import re

import pytest
import numpy as np
import torch

from obp.types import BanditFeedback
from obp.ope import (
    DirectMethod,
    DoublyRobust,
    DoublyRobustWithShrinkage,
    SwitchDoublyRobust,
    SelfNormalizedDoublyRobust,
)
from conftest import generate_action_dist

# prepare instances
dm = DirectMethod()
dr = DoublyRobust()
dr_shrink_0 = DoublyRobustWithShrinkage(lambda_=0.0)
dr_shrink_max = DoublyRobustWithShrinkage(lambda_=1e10)
sndr = SelfNormalizedDoublyRobust()
switch_dr_0 = SwitchDoublyRobust(tau=0.0)
switch_dr_max = SwitchDoublyRobust(tau=1e10)

dr_estimators = [dr, dr_shrink_0, sndr, switch_dr_0]


# dr and self-normalized dr
# action_dist, action, reward, pscore, position, estimated_rewards_by_reg_model, description
invalid_input_of_dr = [
    (
        generate_action_dist(5, 4, 3),
        None,
        np.zeros(5, dtype=int),
        np.ones(5),
        np.random.choice(3, size=5),
        np.zeros((5, 4, 3)),
        "action must be ndarray",
    ),
    (
        generate_action_dist(5, 4, 3),
        np.zeros(5, dtype=int),
        None,
        np.ones(5),
        np.random.choice(3, size=5),
        np.zeros((5, 4, 3)),
        "reward must be ndarray",
    ),
    (
        generate_action_dist(5, 4, 3),
        np.zeros(5, dtype=int),
        np.zeros(5, dtype=int),
        None,
        np.random.choice(3, size=5),
        np.zeros((5, 4, 3)),
        "pscore must be ndarray",
    ),
    (
        generate_action_dist(5, 4, 3),
        np.zeros(5, dtype=int),
        np.zeros(5, dtype=int),
        np.ones(5),
        np.random.choice(3, size=5),
        None,
        "estimated_rewards_by_reg_model must be ndarray",
    ),
    (
        generate_action_dist(5, 4, 3),
        np.zeros(5, dtype=float),
        np.zeros(5, dtype=int),
        np.ones(5),
        np.random.choice(3, size=5),
        np.zeros((5, 4, 3)),
        "action elements must be non-negative integers",
    ),
    (
        generate_action_dist(5, 4, 3),
        np.zeros(5, dtype=int) - 1,
        np.zeros(5, dtype=int),
        np.ones(5),
        np.random.choice(3, size=5),
        np.zeros((5, 4, 3)),
        "action elements must be non-negative integers",
    ),
    (
        generate_action_dist(5, 4, 3),
        "4",
        np.zeros(5, dtype=int),
        np.ones(5),
        np.random.choice(3, size=5),
        np.zeros((5, 4, 3)),
        "action must be ndarray",
    ),
    (
        generate_action_dist(5, 4, 3),
        np.zeros((3, 2), dtype=int),
        np.zeros(5, dtype=int),
        np.ones(5),
        np.random.choice(3, size=5),
        np.zeros((5, 4, 3)),
        "action must be 1-dimensional",
    ),
    (
        generate_action_dist(5, 4, 3),
        np.zeros(5, dtype=int) + 8,
        np.zeros(5, dtype=int),
        np.ones(5),
        np.random.choice(3, size=5),
        np.zeros((5, 4, 3)),
        "action elements must be smaller than the second dimension of action_dist",
    ),
    (
        generate_action_dist(5, 4, 3),
        np.zeros(5, dtype=int),
        "4",
        np.ones(5),
        np.random.choice(3, size=5),
        np.zeros((5, 4, 3)),
        "reward must be ndarray",
    ),
    (
        generate_action_dist(5, 4, 3),
        np.zeros(5, dtype=int),
        np.zeros((3, 2), dtype=int),
        np.ones(5),
        np.random.choice(3, size=5),
        np.zeros((5, 4, 3)),
        "reward must be 1-dimensional",
    ),
    (
        generate_action_dist(5, 4, 3),
        np.zeros(5, dtype=int),
        np.zeros(4, dtype=int),
        np.ones(5),
        np.random.choice(3, size=5),
        np.zeros((5, 4, 3)),
        "action and reward must be the same size.",
    ),
    (
        generate_action_dist(5, 4, 3),
        np.zeros(5, dtype=int),
        np.zeros(5, dtype=int),
        "4",
        np.random.choice(3, size=5),
        np.zeros((5, 4, 3)),
        "pscore must be ndarray",
    ),
    (
        generate_action_dist(5, 4, 3),
        np.zeros(5, dtype=int),
        np.zeros(5, dtype=int),
        np.ones((5, 3)),
        np.random.choice(3, size=5),
        np.zeros((5, 4, 3)),
        "pscore must be 1-dimensional",
    ),
    (
        generate_action_dist(5, 4, 3),
        np.zeros(5, dtype=int),
        np.zeros(5, dtype=int),
        np.ones(4),
        np.random.choice(3, size=5),
        np.zeros((5, 4, 3)),
        "action, reward, and pscore must be the same size.",
    ),
    (
        generate_action_dist(5, 4, 3),
        np.zeros(5, dtype=int),
        np.zeros(5, dtype=int),
        np.arange(5),
        np.random.choice(3, size=5),
        np.zeros((5, 4, 3)),
        "pscore must be positive",
    ),
    (
        generate_action_dist(5, 4, 3),
        np.zeros(5, dtype=int),
        np.zeros(5, dtype=int),
        np.ones(5),
        np.random.choice(3, size=5),
        np.zeros((5, 4, 2)),
        "estimated_rewards_by_reg_model.shape must be the same as action_dist.shape",
    ),
    (
        generate_action_dist(5, 4, 3),
        np.zeros(5, dtype=int),
        np.zeros(5, dtype=int),
        np.ones(5),
        np.random.choice(3, size=5),
        "4",
        "estimated_rewards_by_reg_model must be ndarray",
    ),
]


@pytest.mark.parametrize(
    "action_dist, action, reward, pscore, position, estimated_rewards_by_reg_model, description",
    invalid_input_of_dr,
)
def test_dr_using_invalid_input_data(
    action_dist: np.ndarray,
    action: np.ndarray,
    reward: np.ndarray,
    pscore: np.ndarray,
    position: np.ndarray,
    estimated_rewards_by_reg_model: np.ndarray,
    description: str,
) -> None:
    # estimate_intervals function raises ValueError of all estimators
    for estimator in [dr, sndr]:
        with pytest.raises(ValueError, match=f"{description}*"):
            _ = estimator.estimate_policy_value(
                action_dist=action_dist,
                action=action,
                reward=reward,
                pscore=pscore,
                position=position,
                estimated_rewards_by_reg_model=estimated_rewards_by_reg_model,
            )
        with pytest.raises(ValueError, match=f"{description}*"):
            _ = estimator.estimate_interval(
                action_dist=action_dist,
                action=action,
                reward=reward,
                pscore=pscore,
                position=position,
                estimated_rewards_by_reg_model=estimated_rewards_by_reg_model,
            )


# dr and self-normalized dr
# action_dist, action, reward, pscore, position, estimated_rewards_by_reg_model, description
invalid_input_tensor_of_dr = [
    (
        torch.from_numpy(generate_action_dist(5, 4, 3)),
        None,
        torch.zeros(5, dtype=torch.int64),
        torch.ones(5),
        torch.from_numpy(np.random.choice(3, size=5)),
        torch.zeros((5, 4, 3)),
        "action must be Tensor",
    ),
    (
        torch.from_numpy(generate_action_dist(5, 4, 3)),
        torch.zeros(5, dtype=torch.int64),
        None,
        torch.ones(5),
        torch.from_numpy(np.random.choice(3, size=5)),
        torch.zeros((5, 4, 3)),
        "reward must be Tensor",
    ),
    (
        torch.from_numpy(generate_action_dist(5, 4, 3)),
        torch.zeros(5, dtype=torch.int64),
        torch.zeros(5, dtype=torch.int64),
        None,
        torch.from_numpy(np.random.choice(3, size=5)),
        torch.zeros((5, 4, 3)),
        "pscore must be Tensor",
    ),
    (
        torch.from_numpy(generate_action_dist(5, 4, 3)),
        torch.zeros(5, dtype=torch.int64),
        torch.zeros(5, dtype=torch.int64),
        torch.ones(5),
        torch.from_numpy(np.random.choice(3, size=5)),
        None,
        "estimated_rewards_by_reg_model must be Tensor",
    ),
    (
        torch.from_numpy(generate_action_dist(5, 4, 3)),
        torch.zeros(5, dtype=torch.float32),
        torch.zeros(5, dtype=torch.int64),
        torch.ones(5),
        torch.from_numpy(np.random.choice(3, size=5)),
        torch.zeros((5, 4, 3)),
        "action elements must be non-negative integers",
    ),
    (
        torch.from_numpy(generate_action_dist(5, 4, 3)),
        torch.zeros(5, dtype=torch.int64) - 1,
        torch.zeros(5, dtype=torch.int64),
        torch.ones(5),
        torch.from_numpy(np.random.choice(3, size=5)),
        torch.zeros((5, 4, 3)),
        "action elements must be non-negative integers",
    ),
    (
        torch.from_numpy(generate_action_dist(5, 4, 3)),
        "4",
        torch.zeros(5, dtype=torch.int64),
        torch.ones(5),
        torch.from_numpy(np.random.choice(3, size=5)),
        torch.zeros((5, 4, 3)),
        "action must be Tensor",
    ),
    (
        torch.from_numpy(generate_action_dist(5, 4, 3)),
        torch.zeros((3, 2), dtype=torch.int64),
        torch.zeros(5, dtype=torch.int64),
        torch.ones(5),
        torch.from_numpy(np.random.choice(3, size=5)),
        torch.zeros((5, 4, 3)),
        "action must be 1-dimensional",
    ),
    (
        torch.from_numpy(generate_action_dist(5, 4, 3)),
        torch.zeros(5, dtype=torch.int64) + 8,
        torch.zeros(5, dtype=torch.int64),
        torch.ones(5),
        torch.from_numpy(np.random.choice(3, size=5)),
        torch.zeros((5, 4, 3)),
        "action elements must be smaller than the second dimension of action_dist",
    ),
    (
        torch.from_numpy(generate_action_dist(5, 4, 3)),
        torch.zeros(5, dtype=torch.int64),
        "4",
        torch.ones(5),
        torch.from_numpy(np.random.choice(3, size=5)),
        torch.zeros((5, 4, 3)),
        "reward must be Tensor",
    ),
    (
        torch.from_numpy(generate_action_dist(5, 4, 3)),
        torch.zeros(5, dtype=torch.int64),
        torch.zeros((3, 2), dtype=torch.int64),
        torch.ones(5),
        torch.from_numpy(np.random.choice(3, size=5)),
        torch.zeros((5, 4, 3)),
        "reward must be 1-dimensional",
    ),
    (
        torch.from_numpy(generate_action_dist(5, 4, 3)),
        torch.zeros(5, dtype=torch.int64),
        torch.zeros(4, dtype=torch.int64),
        torch.ones(5),
        torch.from_numpy(np.random.choice(3, size=5)),
        torch.zeros((5, 4, 3)),
        "action and reward must be the same size.",
    ),
    (
        torch.from_numpy(generate_action_dist(5, 4, 3)),
        torch.zeros(5, dtype=torch.int64),
        torch.zeros(5, dtype=torch.int64),
        "4",
        torch.from_numpy(np.random.choice(3, size=5)),
        torch.zeros((5, 4, 3)),
        "pscore must be Tensor",
    ),
    (
        torch.from_numpy(generate_action_dist(5, 4, 3)),
        torch.zeros(5, dtype=torch.int64),
        torch.zeros(5, dtype=torch.int64),
        torch.ones((5, 3)),
        torch.from_numpy(np.random.choice(3, size=5)),
        torch.zeros((5, 4, 3)),
        "pscore must be 1-dimensional",
    ),
    (
        torch.from_numpy(generate_action_dist(5, 4, 3)),
        torch.zeros(5, dtype=torch.int64),
        torch.zeros(5, dtype=torch.int64),
        torch.ones(4),
        torch.from_numpy(np.random.choice(3, size=5)),
        torch.zeros((5, 4, 3)),
        "action, reward, and pscore must be the same size.",
    ),
    (
        torch.from_numpy(generate_action_dist(5, 4, 3)),
        torch.zeros(5, dtype=torch.int64),
        torch.zeros(5, dtype=torch.int64),
        torch.from_numpy(np.arange(5)),
        torch.from_numpy(np.random.choice(3, size=5)),
        torch.zeros((5, 4, 3)),
        "pscore must be positive",
    ),
    (
        torch.from_numpy(generate_action_dist(5, 4, 3)),
        torch.zeros(5, dtype=torch.int64),
        torch.zeros(5, dtype=torch.int64),
        torch.ones(5),
        torch.from_numpy(np.random.choice(3, size=5)),
        torch.zeros((5, 4, 2)),
        "estimated_rewards_by_reg_model.shape must be the same as action_dist.shape",
    ),
    (
        torch.from_numpy(generate_action_dist(5, 4, 3)),
        torch.zeros(5, dtype=torch.int64),
        torch.zeros(5, dtype=torch.int64),
        torch.ones(5),
        torch.from_numpy(np.random.choice(3, size=5)),
        "4",
        "estimated_rewards_by_reg_model must be Tensor",
    ),
]


@pytest.mark.parametrize(
    "action_dist, action, reward, pscore, position, estimated_rewards_by_reg_model, description",
    invalid_input_tensor_of_dr,
)
def test_dr_using_invalid_input_tensor_data(
    action_dist: torch.Tensor,
    action: torch.Tensor,
    reward: torch.Tensor,
    pscore: torch.Tensor,
    position: torch.Tensor,
    estimated_rewards_by_reg_model: torch.Tensor,
    description: str,
) -> None:
    # estimate_intervals function raises ValueError of all estimators
    for estimator in [dr, sndr]:
        with pytest.raises(ValueError, match=f"{description}*"):
            _ = estimator.estimate_policy_value_tensor(
                action_dist=action_dist,
                action=action,
                reward=reward,
                pscore=pscore,
                position=position,
                estimated_rewards_by_reg_model=estimated_rewards_by_reg_model,
            )


# switch-dr

invalid_input_of_switch = [
    ("a", "switching hyperparameter must be float or integer"),
    (-1.0, "switching hyperparameter must be larger than or equal to zero"),
    (np.nan, "switching hyperparameter must not be nan"),
]


@pytest.mark.parametrize(
    "tau, description",
    invalid_input_of_switch,
)
def test_switch_using_invalid_input_data(tau: float, description: str) -> None:
    with pytest.raises(ValueError, match=f"{description}*"):
        _ = SwitchDoublyRobust(tau=tau)


valid_input_of_switch = [
    (3.0, "float tau"),
    (2, "integer tau"),
]


@pytest.mark.parametrize(
    "tau, description",
    valid_input_of_switch,
)
def test_switch_using_valid_input_data(tau: float, description: str) -> None:
    _ = SwitchDoublyRobust(tau=tau)


# dr-os
invalid_input_of_shrinkage = [
    ("a", "shrinkage hyperparameter must be float or integer"),
    (-1.0, "shrinkage hyperparameter must be larger than or equal to zero"),
    (np.nan, "shrinkage hyperparameter must not be nan"),
]


@pytest.mark.parametrize(
    "lambda_, description",
    invalid_input_of_shrinkage,
)
def test_shrinkage_using_invalid_input_data(lambda_: float, description: str) -> None:
    with pytest.raises(ValueError, match=f"{description}*"):
        _ = DoublyRobustWithShrinkage(lambda_=lambda_)


valid_input_of_shrinkage = [
    (3.0, "float lambda_"),
    (2, "integer lambda_"),
]


@pytest.mark.parametrize(
    "lambda_, description",
    valid_input_of_shrinkage,
)
def test_shrinkage_using_valid_input_data(lambda_: float, description: str) -> None:
    _ = DoublyRobustWithShrinkage(lambda_=lambda_)


# dr variants
valid_input_of_dr_variants = [
    (
        generate_action_dist(5, 4, 3),
        np.random.choice(4, size=5),
        np.zeros(5, dtype=int),
        np.random.uniform(low=0.5, high=1.0, size=5),
        np.random.choice(3, size=5),
        np.zeros((5, 4, 3)),
        0.5,
        "all argumnents are given and len_list > 1",
    )
]


@pytest.mark.parametrize(
    "action_dist, action, reward, pscore, position, estimated_rewards_by_reg_model, hyperparameter, description",
    valid_input_of_dr_variants,
)
def test_dr_variants_using_valid_input_data(
    action_dist: np.ndarray,
    action: np.ndarray,
    reward: np.ndarray,
    pscore: np.ndarray,
    position: np.ndarray,
    estimated_rewards_by_reg_model: np.ndarray,
    hyperparameter: float,
    description: str,
) -> None:
    # check dr variants
    switch_dr = SwitchDoublyRobust(tau=hyperparameter)
    dr_os = DoublyRobustWithShrinkage(lambda_=hyperparameter)
    for estimator in [switch_dr, dr_os]:
        est = estimator.estimate_policy_value(
            action_dist=action_dist,
            action=action,
            reward=reward,
            pscore=pscore,
            position=position,
            estimated_rewards_by_reg_model=estimated_rewards_by_reg_model,
        )
        assert est == 0.0, f"policy value must be 0, but {est}"


# dr variants
valid_input_tensor_of_dr_variants = [
    (
        torch.from_numpy(generate_action_dist(5, 4, 3)),
        torch.from_numpy(np.random.choice(4, size=5)),
        torch.zeros(5, dtype=torch.int64),
        torch.from_numpy(np.random.uniform(low=0.5, high=1.0, size=5)),
        torch.from_numpy(np.random.choice(3, size=5)),
        torch.zeros((5, 4, 3)),
        0.5,
        "all argumnents are given and len_list > 1",
    )
]


@pytest.mark.parametrize(
    "action_dist, action, reward, pscore, position, estimated_rewards_by_reg_model, hyperparameter, description",
    valid_input_tensor_of_dr_variants,
)
def test_dr_variants_using_valid_input_tensor_data(
    action_dist: torch.Tensor,
    action: torch.Tensor,
    reward: torch.Tensor,
    pscore: torch.Tensor,
    position: torch.Tensor,
    estimated_rewards_by_reg_model: torch.Tensor,
    hyperparameter: float,
    description: str,
) -> None:
    # check dr variants
    dr_os = DoublyRobustWithShrinkage(lambda_=hyperparameter)
    for estimator in [dr_os]:
        est = estimator.estimate_policy_value_tensor(
            action_dist=action_dist,
            action=action,
            reward=reward,
            pscore=pscore,
            position=position,
            estimated_rewards_by_reg_model=estimated_rewards_by_reg_model,
        )
        assert est.item() == 0.0, f"policy value must be 0, but {est.item()}"


def test_dr_using_random_evaluation_policy(
    synthetic_bandit_feedback: BanditFeedback, random_action_dist: np.ndarray
) -> None:
    """
    Test the format of dr variants using synthetic bandit data and random evaluation policy
    """
    expected_reward = synthetic_bandit_feedback["expected_reward"][:, :, np.newaxis]
    action_dist = random_action_dist
    # prepare input dict
    input_dict = {
        k: v
        for k, v in synthetic_bandit_feedback.items()
        if k in ["reward", "action", "pscore", "position"]
    }
    input_dict["action_dist"] = action_dist
    input_dict["estimated_rewards_by_reg_model"] = expected_reward
    # dr estimtors require all arguments
    for estimator in dr_estimators:
        estimated_policy_value = estimator.estimate_policy_value(**input_dict)
        assert isinstance(
            estimated_policy_value, float
        ), f"invalid type response: {estimator}"
    # remove necessary keys
    del input_dict["reward"]
    del input_dict["pscore"]
    del input_dict["action"]
    del input_dict["estimated_rewards_by_reg_model"]
    for estimator in dr_estimators:
        with pytest.raises(
            TypeError,
            match=re.escape(
                "estimate_policy_value() missing 4 required positional arguments: 'reward', 'action', 'pscore', and 'estimated_rewards_by_reg_model'"
            ),
        ):
            _ = estimator.estimate_policy_value(**input_dict)

    # prepare input dict
    input_tensor_dict = {
        k: v if v is None else torch.from_numpy(v)
        for k, v in synthetic_bandit_feedback.items()
        if k in ["reward", "action", "pscore", "position"]
    }
    input_tensor_dict["action_dist"] = torch.from_numpy(action_dist)
    input_tensor_dict["estimated_rewards_by_reg_model"] = torch.from_numpy(
        expected_reward
    )
    # dr estimtors require all arguments
    for estimator in dr_estimators:
        if estimator.estimator_name == "switch-dr":
            with pytest.raises(
                NotImplementedError,
                match=re.escape(
                    "This is not implemented for Swtich-DR because it is indifferentiable."
                ),
            ):
                _ = estimator.estimate_policy_value_tensor(**input_tensor_dict)
        else:
            estimated_policy_value = estimator.estimate_policy_value_tensor(
                **input_tensor_dict
            )
            assert isinstance(
                estimated_policy_value, torch.Tensor
            ), f"invalid type response: {estimator}"
    # remove necessary keys
    del input_tensor_dict["reward"]
    del input_tensor_dict["pscore"]
    del input_tensor_dict["action"]
    del input_tensor_dict["estimated_rewards_by_reg_model"]
    for estimator in dr_estimators:
        if estimator.estimator_name == "switch-dr":
            with pytest.raises(
                NotImplementedError,
                match=re.escape(
                    "This is not implemented for Swtich-DR because it is indifferentiable."
                ),
            ):
                _ = estimator.estimate_policy_value_tensor(**input_tensor_dict)
        else:
            with pytest.raises(
                TypeError,
                match=re.escape(
                    "estimate_policy_value_tensor() missing 4 required positional arguments: 'reward', 'action', 'pscore', and 'estimated_rewards_by_reg_model'"
                ),
            ):
                _ = estimator.estimate_policy_value_tensor(**input_tensor_dict)


def test_boundedness_of_sndr_using_random_evaluation_policy(
    synthetic_bandit_feedback: BanditFeedback, random_action_dist: np.ndarray
) -> None:
    """
    Test the boundedness of sndr estimators using synthetic bandit data and random evaluation policy
    """
    expected_reward = synthetic_bandit_feedback["expected_reward"][:, :, np.newaxis]
    action_dist = random_action_dist
    # prepare input dict
    input_dict = {
        k: v
        for k, v in synthetic_bandit_feedback.items()
        if k in ["reward", "action", "pscore", "position"]
    }
    input_dict["action_dist"] = action_dist
    input_dict["estimated_rewards_by_reg_model"] = expected_reward
    # make pscore too small (to check the boundedness of sndr)
    input_dict["pscore"] = input_dict["pscore"] ** 3
    estimated_policy_value = sndr.estimate_policy_value(**input_dict)
    assert (
        estimated_policy_value <= 2
    ), f"estimated policy value of sndr should be smaller than or equal to 2 (because of its 2-boundedness), but the value is: {estimated_policy_value}"

    # prepare input dict
    input_tensor_dict = {
        k: v if v is None else torch.from_numpy(v)
        for k, v in synthetic_bandit_feedback.items()
        if k in ["reward", "action", "pscore", "position"]
    }
    input_tensor_dict["action_dist"] = torch.from_numpy(action_dist)
    input_tensor_dict["estimated_rewards_by_reg_model"] = torch.from_numpy(
        expected_reward
    )
    # make pscore too small (to check the boundedness of sndr)
    input_tensor_dict["pscore"] = input_tensor_dict["pscore"] ** 3
    estimated_policy_value = sndr.estimate_policy_value_tensor(**input_tensor_dict)
    assert (
        estimated_policy_value.item() <= 2
    ), f"estimated policy value of sndr should be smaller than or equal to 2 (because of its 2-boundedness), but the value is: {estimated_policy_value.item()}"


def test_dr_shrinkage_using_random_evaluation_policy(
    synthetic_bandit_feedback: BanditFeedback, random_action_dist: np.ndarray
) -> None:
    """
    Test the dr shrinkage estimators using synthetic bandit data and random evaluation policy
    """
    expected_reward = synthetic_bandit_feedback["expected_reward"][:, :, np.newaxis]
    action_dist = random_action_dist
    # prepare input dict
    input_dict = {
        k: v
        for k, v in synthetic_bandit_feedback.items()
        if k in ["reward", "action", "pscore", "position"]
    }
    input_dict["action_dist"] = action_dist
    input_dict["estimated_rewards_by_reg_model"] = expected_reward
    dm_value = dm.estimate_policy_value(**input_dict)
    dr_value = dr.estimate_policy_value(**input_dict)
    dr_shrink_0_value = dr_shrink_0.estimate_policy_value(**input_dict)
    dr_shrink_max_value = dr_shrink_max.estimate_policy_value(**input_dict)
    assert (
        dm_value == dr_shrink_0_value
    ), "DoublyRobustWithShrinkage (lambda=0) should be the same as DirectMethod"
    assert (
        np.abs(dr_value - dr_shrink_max_value) < 1e-5
    ), "DoublyRobustWithShrinkage (lambda=inf) should be almost the same as DoublyRobust"

    # prepare input dict
    input_tensor_dict = {
        k: v if v is None else torch.from_numpy(v)
        for k, v in synthetic_bandit_feedback.items()
        if k in ["reward", "action", "pscore", "position"]
    }
    input_tensor_dict["action_dist"] = torch.from_numpy(action_dist)
    input_tensor_dict["estimated_rewards_by_reg_model"] = torch.from_numpy(
        expected_reward
    )
    dm_value = dm.estimate_policy_value_tensor(**input_tensor_dict)
    dr_value = dr.estimate_policy_value_tensor(**input_tensor_dict)
    dr_shrink_0_value = dr_shrink_0.estimate_policy_value_tensor(**input_tensor_dict)
    dr_shrink_max_value = dr_shrink_max.estimate_policy_value_tensor(
        **input_tensor_dict
    )
    assert (
        dm_value.item() == dr_shrink_0_value.item()
    ), "DoublyRobustWithShrinkage (lambda=0) should be the same as DirectMethod"
    assert (
        np.abs(dr_value.item() - dr_shrink_max_value.item()) < 1e-5
    ), "DoublyRobustWithShrinkage (lambda=inf) should be almost the same as DoublyRobust"


def test_switch_dr_using_random_evaluation_policy(
    synthetic_bandit_feedback: BanditFeedback, random_action_dist: np.ndarray
) -> None:
    """
    Test the switch_dr using synthetic bandit data and random evaluation policy
    """
    expected_reward = synthetic_bandit_feedback["expected_reward"][:, :, np.newaxis]
    action_dist = random_action_dist
    # prepare input dict
    input_dict = {
        k: v
        for k, v in synthetic_bandit_feedback.items()
        if k in ["reward", "action", "pscore", "position"]
    }
    input_dict["action_dist"] = action_dist
    input_dict["estimated_rewards_by_reg_model"] = expected_reward
    dm_value = dm.estimate_policy_value(**input_dict)
    dr_value = dr.estimate_policy_value(**input_dict)
    switch_dr_0_value = switch_dr_0.estimate_policy_value(**input_dict)
    switch_dr_max_value = switch_dr_max.estimate_policy_value(**input_dict)
    assert (
        dm_value == switch_dr_0_value
    ), "SwitchDR (tau=0) should be the same as DirectMethod"
    assert (
        dr_value == switch_dr_max_value
    ), "SwitchDR (tau=1e10) should be the same as DoublyRobust"
