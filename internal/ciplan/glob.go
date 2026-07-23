// Copyright (c) 2026 VEXXHOST, Inc.
// SPDX-License-Identifier: Apache-2.0

package ciplan

import (
	"fmt"
	"regexp"
	"strings"
)

// compileGlob supports repository-oriented globs. A single star does not
// cross a path separator; a double star does.
func compileGlob(pattern string) (*regexp.Regexp, error) {
	if pattern == "" {
		return nil, fmt.Errorf("glob must not be empty")
	}
	if strings.HasPrefix(pattern, "/") {
		return nil, fmt.Errorf("glob must be repository-relative")
	}

	var expression strings.Builder
	expression.WriteString("^")
	for index := 0; index < len(pattern); {
		switch pattern[index] {
		case '*':
			if index+1 < len(pattern) && pattern[index+1] == '*' {
				expression.WriteString(".*")
				index += 2
			} else {
				expression.WriteString("[^/]*")
				index++
			}
		case '?':
			expression.WriteString("[^/]")
			index++
		case '[', ']':
			return nil, fmt.Errorf("character classes are not supported")
		default:
			expression.WriteString(regexp.QuoteMeta(pattern[index : index+1]))
			index++
		}
	}
	expression.WriteString("$")

	compiled, err := regexp.Compile(expression.String())
	if err != nil {
		return nil, fmt.Errorf("compiling glob: %w", err)
	}
	return compiled, nil
}
