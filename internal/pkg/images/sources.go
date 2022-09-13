package images

import (
	"fmt"

	"github.com/spf13/viper"
)

func GetRepository(image, repository string) string {
	var imageKey string

	if viper.IsSet("images.global.repository") {
		imageKey = "images.global.repository"
	} else {
		imageKey = fmt.Sprintf("images.%s.repository", image)
	}

	if len(imageKey) > 0 && viper.IsSet(imageKey) {
		repository = viper.GetString(imageKey)
	}

	return repository
}

func GetReference(image, repository, tag string) string {
	repository = GetRepository(image, repository)

	return fmt.Sprintf("%s:%s", repository, tag)
}
