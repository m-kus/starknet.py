# pylint: disable=redefined-outer-name

import pytest
import pytest_asyncio

from starknet_py.compile.compiler import Compiler
from starknet_py.constants import FEE_CONTRACT_ADDRESS, DEVNET_FEE_CONTRACT_ADDRESS
from starknet_py.contract import Contract
from starknet_py.net import AccountClient
from starknet_py.tests.e2e.fixtures.constants import CONTRACTS_DIR, MAX_FEE
from starknet_py.tests.e2e.fixtures.misc import read_contract


@pytest.fixture(
    scope="module", params=["deploy_map_contract", "new_deploy_map_contract"]
)
def map_contract(request) -> Contract:
    """
    Returns account contracts using old and new account versions
    """
    return request.getfixturevalue(request.param)


@pytest.fixture(scope="module")
def map_source_code() -> str:
    """
    Returns source code of the map contract
    """
    return read_contract("map.cairo", directory=CONTRACTS_DIR)


@pytest.fixture(scope="module")
def map_compiled_contract() -> str:
    """
    Returns compiled map contract
    """
    return read_contract("map_compiled.json")


@pytest.fixture(scope="module")
def erc20_compiled_contract() -> str:
    """
    Returns compiled erc20 contract
    """
    return read_contract("erc20_compiled.json")


@pytest.fixture(scope="module")
def base_compiled_contract() -> str:
    """
    Returns compiled base contract
    """
    return read_contract("base_compiled.json")


@pytest.fixture(scope="module")
def constructor_with_arguments_compiled_contract() -> str:
    """
    Returns compiled constructor_with_arguments contract
    """
    return read_contract("constructor_with_arguments_compiled.json")


@pytest.fixture(scope="module")
def constructor_without_arguments_compiled_contract() -> str:
    """
    Returns compiled constructor_without_arguments contract
    """
    return read_contract("constructor_without_arguments_compiled.json")


async def deploy_contract(
    account_client: AccountClient, compiled_contract: str
) -> Contract:
    """
    Deploys a contract and returns its instance
    """
    deployment_result = await Contract.deploy(
        client=account_client, compiled_contract=compiled_contract
    )
    deployment_result = await deployment_result.wait_for_acceptance()
    return deployment_result.deployed_contract


@pytest_asyncio.fixture(scope="module")
async def deploy_map_contract(
    gateway_account_client: AccountClient, map_compiled_contract: str
) -> Contract:
    """
    Deploys map contract and returns its instance
    """
    return await deploy_contract(gateway_account_client, map_compiled_contract)


@pytest_asyncio.fixture(scope="module")
async def new_deploy_map_contract(
    new_gateway_account_client: AccountClient, map_compiled_contract: str
) -> Contract:
    """
    Deploys new map contract and returns its instance
    """
    return await deploy_contract(new_gateway_account_client, map_compiled_contract)


@pytest_asyncio.fixture(name="erc20_contract", scope="module")
async def deploy_erc20_contract(
    gateway_account_client: AccountClient, erc20_compiled_contract: str
) -> Contract:
    """
    Deploys erc20 contract and returns its instance
    """
    return await deploy_contract(gateway_account_client, erc20_compiled_contract)


@pytest.fixture(scope="module")
def fee_contract(pytestconfig, new_gateway_account_client: AccountClient) -> Contract:
    """
    Returns an instance of the fee contract. It is used to transfer tokens
    """
    abi = [
        {
            "inputs": [
                {"name": "recipient", "type": "felt"},
                {"name": "amount", "type": "Uint256"},
            ],
            "name": "transfer",
            "outputs": [{"name": "success", "type": "felt"}],
            "type": "function",
        },
        {
            "members": [
                {"name": "low", "offset": 0, "type": "felt"},
                {"name": "high", "offset": 1, "type": "felt"},
            ],
            "name": "Uint256",
            "size": 2,
            "type": "struct",
        },
    ]

    address = (
        FEE_CONTRACT_ADDRESS
        if pytestconfig.getoption("--net") != "devnet"
        else DEVNET_FEE_CONTRACT_ADDRESS
    )

    return Contract(
        address=address,
        abi=abi,
        client=new_gateway_account_client,
    )


@pytest.fixture(name="balance_contract")
def fixture_balance_contract() -> str:
    """
    Returns compiled code of the balance.cairo contract
    """
    return read_contract("balance_compiled.json")


@pytest_asyncio.fixture(scope="module")
async def account_with_validate_deploy_class_hash(
    new_gateway_account_client: AccountClient,
) -> int:
    """
    Returns a class_hash of the account_with_validate_deploy.cairo
    """
    compiled_contract = Compiler(
        contract_source=read_contract(
            "account_with_validate_deploy.cairo", directory=CONTRACTS_DIR
        ),
        is_account_contract=True,
    ).compile_contract()

    declare_tx = await new_gateway_account_client.sign_declare_transaction(
        compiled_contract=compiled_contract,
        max_fee=MAX_FEE,
    )
    resp = await new_gateway_account_client.declare(transaction=declare_tx)
    await new_gateway_account_client.wait_for_tx(resp.transaction_hash)

    return resp.class_hash
