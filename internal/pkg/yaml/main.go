package yaml

import (
	"bytes"

	"gopkg.in/yaml.v3"
)

func Marshall(v interface{}) ([]byte, error) {
	var b bytes.Buffer

	encoder := yaml.NewEncoder(&b)
	encoder.SetIndent(2)
	err := encoder.Encode(v)
	if err != nil {
		return nil, err
	}

	return b.Bytes(), nil
}

func MarshallToString(v interface{}) (string, error) {
	bytes, err := Marshall(v)
	if err != nil {
		return "", err
	}

	return string(bytes), nil
}
