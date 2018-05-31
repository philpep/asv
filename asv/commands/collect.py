# -*- coding: utf-8 -*-
# Licensed under a 3-clause BSD style license - see LICENSE.rst

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import itertools

from ..benchmarks import Benchmarks
from ..benchmarks import _format_benchmark_result
from ..machine import Machine
from ..results import iter_results_for_machine_and_hash
from ..repo import get_repo
from .. import environment
from . import Command
from . import common_args
from ..console import log


class Collect(Command):

    @classmethod
    def setup_arguments(cls, subparsers):
        parser = subparsers.add_parser('collect', help=(
            'Collect benchmark suite and display results'))
        parser.add_argument(
            'range', nargs='?', default=None,
            help='Also display results for given range of commits')
        common_args.add_bench(parser)
        parser.set_defaults(func=cls.run_from_args)
        return parser

    @classmethod
    def run_from_conf_args(cls, conf, args, **kwargs):
        return cls.run(conf=conf, bench=args.bench, range_spec=args.range)

    @classmethod
    def run(cls, conf, bench=None, range_spec=None):
        repo = get_repo(conf)
        if range_spec is None:
            commit_hashes = list(set([repo.get_hash_from_name(branch)
                                      for branch in conf.branches]))
        else:
            commit_hashes = repo.get_hashes_from_range(range_spec)
        environments = list(environment.get_environments(
            conf, ['existing:same']))
        benchmarks = Benchmarks.discover(conf, repo, environments,
                                         commit_hashes, regex=bench)
        machine = Machine.load()
        for commit_hash in commit_hashes:
            result = list(iter_results_for_machine_and_hash(
                conf.results_dir, machine.machine, commit_hash))
            result = result[0] if result else None
            for _, benchmark in sorted(benchmarks.items()):
                display_result = None
                if result is not None:
                    name, params = benchmark['name'], benchmark['params']
                    try:
                        display_result = [
                            (v, None)
                            for v in result.get_result_value(name, params)]
                    except KeyError:
                        pass
                if display_result is None:
                    display_result = [
                        (float('nan'), None) for _ in itertools.product(
                            *benchmark['params'])]
                display = _format_benchmark_result(display_result, benchmark)
                log.info((
                    benchmark['name'] + " for commit " + commit_hash[:7] +
                    ":\n" + "\n".join(display)))
