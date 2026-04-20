from __future__ import annotations

import os
import shutil
import subprocess
import textwrap
from pathlib import Path

from tools.helper_contract_registry import HELPER_CONTRACTS


def _cpp_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _generate_cpp_source(contracts: list[dict]) -> str:
    include_headers = sorted({contract["include_header"] for contract in contracts})
    includes = "\n".join(f'#include "{header}"' for header in include_headers)

    contract_blocks: list[str] = []
    for contract in contracts:
        section_blocks: list[str] = []
        for section in contract["schema_sections"]:
            functions_expr = f'{contract["helper_type"]}::{section["functions_accessor"]}'
            events_expr = f'{contract["helper_type"]}::{section["events_accessor"]}'
            name_type = section.get("name_type") or contract["helper_type"]
            name_expr = f'{name_type}::get_name()'
            section_blocks.append(
                textwrap.dedent(
                    f"""\
                    {{
                        boost::json::object section_obj;
                        section_obj["key"] = "{_cpp_escape(section["key"])}";
                        section_obj["service_name"] = std::string({name_expr});
                        section_obj["functions"] = serialize_functions({functions_expr});
                        section_obj["events"] = serialize_events({events_expr});
                        sections.emplace_back(std::move(section_obj));
                    }}
                    """
                ).rstrip()
            )

        contract_blocks.append(
            textwrap.dedent(
                f"""\
                {{
                    boost::json::array sections;
                {textwrap.indent(chr(10).join(section_blocks), "    ")}

                    boost::json::object contract_obj;
                    contract_obj["category"] = "{_cpp_escape(contract["category"])}";
                    contract_obj["slug"] = "{_cpp_escape(contract["slug"])}";
                    contract_obj["header_path"] = "{_cpp_escape(contract["header_path"])}";
                    contract_obj["include_header"] = "{_cpp_escape(contract["include_header"])}";
                    contract_obj["helper_type"] = "{_cpp_escape(contract["helper_type"])}";
                    contract_obj["sections"] = std::move(sections);
                    write_json_file(out_dir / "{_cpp_escape(contract["category"])}" / "{_cpp_escape(contract["slug"])}.json", contract_obj);
                }}
                """
            ).rstrip()
        )

    return textwrap.dedent(
        f"""\
        #define BOOST_ALL_NO_LIB 1
        #define BOOST_ERROR_CODE_HEADER_ONLY 1
        #define BOOST_JSON_NO_LIB 1
        #include <iostream>
        #include "boost/json/src.hpp"
        #include "schema_json_serializer.hpp"
        {includes}

        using brookesia_host::serialize_functions;
        using brookesia_host::serialize_events;
        using brookesia_host::write_json_file;

        namespace fs = std::filesystem;

        int main(int argc, char **argv)
        {{
            if (argc != 2) {{
                std::cerr << "Usage: " << argv[0] << " <output-dir>" << std::endl;
                return 1;
            }}

            fs::path out_dir = argv[1];
            fs::create_directories(out_dir);

        {textwrap.indent(chr(10).join(contract_blocks), "    ")}

            return 0;
        }}
        """
    )


def _iter_boost_include_paths(repo_root: Path) -> list[Path]:
    candidates: list[Path] = []

    for env_var in ("BOOST_INCLUDEDIR", "BOOST_ROOT"):
        env_value = os.environ.get(env_var, "").strip()
        if not env_value:
            continue
        path = Path(env_value)
        if env_var == "BOOST_ROOT" and not (path / "boost").exists() and (path / "include" / "boost").exists():
            path = path / "include"
        candidates.append(path)

    tools_dir = repo_root / ".tools"
    if tools_dir.is_dir():
        for path in sorted(tools_dir.glob("boost_*"), reverse=True):
            candidates.append(path)
            include_path = path / "include"
            if include_path.is_dir():
                candidates.append(include_path)

    candidates.append(Path("/usr/local/include"))

    include_paths: list[Path] = []
    seen: set[str] = set()
    for path in candidates:
        resolved = path.resolve(strict=False)
        key = os.path.normcase(str(resolved))
        if key in seen:
            continue
        if (resolved / "boost" / "json.hpp").is_file():
            include_paths.append(resolved)
            seen.add(key)

    return include_paths


def _is_msvc_compiler(compiler: str) -> bool:
    return Path(compiler).name.lower() in {"cl", "cl.exe"}


def _compile_exporter(repo_root: Path, cpp_path: Path, binary_path: Path, context: str = "") -> None:
    boost_include_paths = _iter_boost_include_paths(repo_root)
    if not boost_include_paths:
        raise RuntimeError(
            "Boost headers were not found. Set BOOST_ROOT/BOOST_INCLUDEDIR or place boost_* under repo/.tools."
        )

    include_paths = [
        *boost_include_paths,
        repo_root / "utils" / "brookesia_lib_utils" / "include",
        repo_root / "service" / "brookesia_service_helper" / "include",
        repo_root / "service" / "brookesia_service_helper" / "host_test",
        repo_root / "service" / "brookesia_service_manager" / "include",
        repo_root / "agent" / "brookesia_agent_helper" / "include",
    ]

    preferred = os.environ.get("CXX", "").strip()
    if preferred:
        compiler_candidates = [preferred]
    else:
        compiler_candidates = [
            "c++",
            "g++",
            "clang++",
            "g++-13",
            "g++-12",
            "clang++-17",
            "clang++-16",
        ]
    compilers: list[str] = []
    for candidate in compiler_candidates:
        if candidate in compilers:
            continue
        if shutil.which(candidate):
            compilers.append(candidate)

    standard_flags = ["-std=c++23", "-std=c++2b"]
    errors: list[str] = []
    for compiler in compilers:
        is_msvc = _is_msvc_compiler(compiler)
        if is_msvc:
            output_path = binary_path.with_suffix(".exe")
            standard_flags = ["/std:c++latest", "/std:c++20"]
        else:
            output_path = binary_path
            standard_flags = ["-std=c++23", "-std=c++2b"]

        for standard_flag in standard_flags:
            if is_msvc:
                compile_command = [compiler, "/nologo", standard_flag, "/EHsc", str(cpp_path)]
                for include_path in include_paths:
                    compile_command.extend(["/I", str(include_path)])
                compile_command.append(f"/Fe:{output_path}")
            else:
                compile_command = [compiler, standard_flag, str(cpp_path)]
                for include_path in include_paths:
                    compile_command.extend(["-I", str(include_path)])
                compile_command.extend(["-pthread", "-o", str(output_path)])
            result = subprocess.run(
                compile_command,
                cwd=repo_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            if result.returncode == 0:
                return

            output_lines = [
                line.rstrip()
                for line in (result.stdout.splitlines() + result.stderr.splitlines())
                if line.strip()
            ]
            if output_lines:
                if len(output_lines) <= 6:
                    summary = " | ".join(output_lines)
                else:
                    summary = " | ".join(output_lines[:3] + ["..."] + output_lines[-2:])
            else:
                summary = f"exit code {result.returncode}"
            errors.append(f"{compiler} {standard_flag}: {summary}")

    if not compilers:
        raise RuntimeError("No C++ compiler found. Set CXX or install c++/g++/clang++ for docs schema export.")

    details = "\n".join(errors[-8:])
    raise RuntimeError(
        f"Failed to compile helper schema exporter with available compilers/standards{f' ({context})' if context else ''}. "
        "Please provide a compiler that supports C++23 (or C++2b with std::expected).\n"
        f"{details}"
    )


def export_helper_schemas(repo_root: Path, build_dir: Path, output_dir: Path) -> None:
    work_dir = build_dir / "contract_tools"
    work_dir.mkdir(parents=True, exist_ok=True)

    for contract in HELPER_CONTRACTS:
        slug = f"{contract['category']}_{contract['slug']}"
        cpp_path = work_dir / f"helper_schema_exporter_{slug}.cpp"
        binary_path = work_dir / f"helper_schema_exporter_{slug}"
        if os.name == "nt":
            binary_path = binary_path.with_suffix(".exe")
        cpp_path.write_text(_generate_cpp_source([contract]), encoding="utf-8")

        _compile_exporter(
            repo_root=repo_root,
            cpp_path=cpp_path,
            binary_path=binary_path,
            context=slug,
        )
        subprocess.run([str(binary_path), str(output_dir)], check=True, cwd=repo_root)
