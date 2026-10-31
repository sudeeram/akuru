import test from 'node:test';
import assert from 'node:assert/strict';
import {isSupportedNode} from '../../scripts/node-version-policy.mjs';

test('rejects affected patches, EOL/odd and unreviewed release lines', () => {
  for (const version of ['v20.20.0','22.13.0','22.23.2','22.23.3','24.19.0','24.22.0','26.12.0','23.99.99','25.1.0','28.0.0']) {
    assert.equal(isSupportedNode(version), false, version);
  }
});
test('accepts security floors and newer patches/minors in reviewed lines', () => {
  for (const version of ['22.23.4','v22.23.5','22.24.0','24.22.1','v24.23.0','26.12.1','26.13.0']) {
    assert.equal(isSupportedNode(version), true, version);
  }
});
test('rejects malformed, prerelease and incomplete versions', () => {
  for (const version of ['22','22.23','22.23.4-beta.1','v22.23.4-extra','latest','', '22.23.4\n24.22.1']) {
    assert.equal(isSupportedNode(version), false, version);
  }
});
