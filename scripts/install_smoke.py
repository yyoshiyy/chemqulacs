"""Offline smoke test for the standard install."""
from importlib.metadata import metadata, version
from math import isclose

from braket.devices import LocalSimulator
from pyscf import gto, lib, mcscf, scf
from quri_parts.algo.optimizer import LBFGS
from quri_parts.braket.backend import BraketSamplingBackend
from quri_parts.circuit import QuantumCircuit
from quri_parts_oqtopus.backend import OqtopusSamplingBackend  # noqa: F401
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2  # noqa: F401

from chemqulacs.vqe.vqeci import Ansatz
from chemqulacs.vqe.vqemcscf import VQECASCI

EXPECTED = {
    "chemqulacs": "0.1.0",
    "quri-parts-core": "0.20.3",
    "quri-parts-circuit": "0.20.3",
    "quri-parts-openqasm": "0.20.3",
    "quri-parts-rust": "0.20.3",
    "quri-parts-oqtopus": "1.1.5",
    "oqtopus-client": "1.1.6",
    "qiskit": "1.4.6",
    "qiskit-ibm-runtime": "0.22.0",
    "ibm-cloud-sdk-core": "3.18.0",
    "ibm-platform-services": "0.48.0",
    "numpy": "1.26.4",
    "scipy": "1.13.1",
    "qulacs": "0.6.14",
    "openfermion": "1.8.1",
    "pyscf": "2.12.1",
}


def main():
    assert not metadata("chemqulacs").get_all("Provides-Extra")
    for name, expected in EXPECTED.items():
        actual = version(name)
        assert actual == expected, f"{name}: {actual} != {expected}"
        print(f"{name}: {actual}")
    print(f"urllib3 (resolved transitively): {version('urllib3')}")

    circuit = QuantumCircuit(1)
    circuit.add_X_gate(0)
    counts = BraketSamplingBackend(LocalSimulator()).sample(circuit, 16).result().counts
    assert dict(counts) == {1: 16}, counts
    print("QURI Parts + Braket local simulator: 16/16 shots in |1>")

    lib.num_threads(1)
    mol = gto.M(atom="H 0 0 0; H 0 0 0.74", basis="sto-3g", verbose=0)
    mf = scf.RHF(mol).run()
    assert mf.converged
    exact = mcscf.CASCI(mf, 2, 2).run().e_tot
    vqe = VQECASCI(mf, 2, 2, optimizer=LBFGS(), ansatz=Ansatz.GateFabric, layers=2)
    vqe.kernel()
    assert isclose(vqe.e_tot, exact, abs_tol=1e-6, rel_tol=0), (vqe.e_tot, exact)
    print(f"H2 VQE-CASCI: {vqe.e_tot:.10f} Ha (exact CASCI: {exact:.10f} Ha)")


if __name__ == "__main__":
    main()
