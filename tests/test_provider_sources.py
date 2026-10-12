"""Citations select exact bound sources; checksums never depend on model transcription."""
import copy
import io
import unittest
from unittest.mock import patch
import urllib.error
from pathlib import Path
from evaluator import intake, provider

ROOT = Path(__file__).resolve().parents[1]


class ProviderSources(unittest.TestCase):
    def setUp(self):
        self.record = intake.build_evidence(ROOT, intake.TRACKS[0])
        self.path = 'candidate/proof.md'

    def test_citation_binds_exact_file_without_changing_requested_range(self):
        item = {'citations':[{'path':self.path,'lines':[1,2]}]}
        provider.bind_citations(item, self.record)
        self.assertEqual(item['citations'][0], {'path':self.path,'lines':[1,2],
            'sha256':self.record['evidence']['files'][self.path]['sha256']})
        sources = provider.source_view(self.record)['sources']
        self.assertEqual(sources[self.path]['numbered_text'].splitlines()[0],
                         '1: '+self.record['evidence']['files'][self.path]['text'].splitlines()[0])

    def test_range_errors_unknown_sources_and_model_supplied_hashes_are_refused(self):
        maximum = len(self.record['evidence']['files'][self.path]['text'].splitlines())
        cases = [{'path':self.path,'lines':[1,maximum+1]},
                 {'path':self.path,'lines':[2,1]}, {'path':self.path,'lines':[0,1]},
                 {'path':'candidate/missing.md','lines':[1,1]},
                 {'path':self.path,'lines':[1,1],'sha256':'0'*64}]
        for citation in cases:
            with self.subTest(citation=citation), self.assertRaises(ValueError):
                provider.bind_citations({'citations':[copy.deepcopy(citation)]}, self.record)

    def test_structured_schema_constrains_each_source_to_its_actual_line_limit(self):
        schema = provider.response_schema('cost', self.record)
        choices = schema['properties']['obligations']['items']['properties']['citations']['items']['anyOf']
        choice = next(c for c in choices if c['properties']['path']['enum']==[self.path])
        self.assertEqual(set(choice['properties']), {'path','lines'})
        self.assertEqual(choice['properties']['lines']['items']['maximum'],
                         len(self.record['evidence']['files'][self.path]['text'].splitlines()))

    def test_http_failure_preserves_status_without_credentials_or_error_body(self):
        class FailedOpener:
            def open(self, request, timeout):
                raise urllib.error.HTTPError(request.full_url, 402, 'private-provider-message',
                    {}, io.BytesIO(b'private-provider-body'))
        attempts = []
        with patch('urllib.request.build_opener', return_value=FailedOpener()), self.assertRaises(ValueError):
            provider.completion({'endpoint':'https://openrouter.ai/api/v1/chat/completions',
                'max_tokens':16000,'timeout_seconds':600}, 'vendor/model', [], {}, 'private-api-key',
                audit=attempts.append)
        self.assertEqual(attempts[0]['transport_failure'], {'kind':'http','status':402})
        self.assertNotIn('private', str(attempts))


if __name__ == '__main__':
    unittest.main()
