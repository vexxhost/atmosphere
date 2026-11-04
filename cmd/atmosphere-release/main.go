// Command atmosphere-release generates, publishes, inspects and mirrors
// Atmosphere release manifests.
package main

import (
	"context"
	"errors"
	"fmt"
	"os"
	"os/exec"
	"strings"

	log "github.com/sirupsen/logrus"
	"github.com/spf13/cobra"
	"oras.land/oras-go/v2/errdef"

	"github.com/goccy/go-yaml"
	"github.com/vexxhost/atmosphere/internal/releasemanifest"
)

const (
	defaultVarsPath     = "roles/defaults/vars/main.yml"
	defaultDefaultsPath = "roles/defaults/defaults/main.yml"
	defaultSource       = "https://github.com/vexxhost/atmosphere"
)

type globalOptions struct {
	plainHTTP bool
}

func main() {
	if err := newRootCommand().Execute(); err != nil {
		log.Fatal(err)
	}
}

func newRootCommand() *cobra.Command {
	opts := &globalOptions{}

	root := &cobra.Command{
		Use:           "atmosphere-release",
		Short:         "Generate, publish, inspect and mirror Atmosphere release manifests",
		SilenceUsage:  true,
		SilenceErrors: true,
	}
	root.PersistentFlags().BoolVar(&opts.plainHTTP, "plain-http", false, "use HTTP instead of HTTPS for registries (local test registries only)")

	root.AddCommand(
		newGenerateCommand(),
		newWriteVarsCommand(opts),
		newPushCommand(opts),
		newDigestCommand(),
		newPublishCommand(opts),
		newPromoteCommand(opts),
		newShowCommand(opts),
		newDiffCommand(opts),
		newCheckCommand(opts),
		newMirrorCommand(opts),
	)
	return root
}

func (o *globalOptions) factory() (releasemanifest.TargetFactory, error) {
	return releasemanifest.NewRemoteFactory(releasemanifest.RemoteOptions{PlainHTTP: o.plainHTTP})
}

func (o *globalOptions) load(ctx context.Context, location string) (*releasemanifest.Manifest, error) {
	factory, err := o.factory()
	if err != nil {
		return nil, err
	}
	return releasemanifest.Load(ctx, location, factory)
}

func currentCommit() string {
	if sha := os.Getenv("GITHUB_SHA"); sha != "" {
		return sha
	}
	out, err := exec.Command("git", "rev-parse", "HEAD").Output()
	if err != nil {
		return ""
	}
	return strings.TrimSpace(string(out))
}

func generate(ctx context.Context, varsPath, defaultsPath, commit, resolvePrefix string) (*releasemanifest.Manifest, error) {
	src, err := releasemanifest.LoadSource(varsPath, defaultsPath)
	if err != nil {
		return nil, err
	}
	if commit == "" {
		commit = currentCommit()
	}
	return releasemanifest.Generate(ctx, src, releasemanifest.DockerResolver{}, releasemanifest.GenerateOptions{
		Commit:        commit,
		ResolvePrefix: resolvePrefix,
	})
}

func newGenerateCommand() *cobra.Command {
	var varsPath, defaultsPath, commit, output, resolvePrefix string
	var writeVars bool

	cmd := &cobra.Command{
		Use:   "generate",
		Short: "Resolve every image in the source tree into a release manifest",
		Long: `Render the image list in the defaults role, keep existing digest pins and
resolve every image referenced only by tag to the digest it currently points to.`,
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, _ []string) error {
			m, err := generate(cmd.Context(), varsPath, defaultsPath, commit, resolvePrefix)
			if err != nil {
				return err
			}
			data, err := m.Marshal()
			if err != nil {
				return err
			}

			if output == "" || output == "-" {
				_, err = os.Stdout.Write(data)
			} else {
				err = os.WriteFile(output, data, 0o644)
				log.WithField("images", len(m.Images)).Infof("Wrote %s", output)
			}
			if err != nil {
				return err
			}

			if writeVars {
				if err := releasemanifest.WriteVars(varsPath, m); err != nil {
					return err
				}
				log.Infof("Pinned images in %s", varsPath)
			}
			return nil
		},
	}
	cmd.Flags().StringVar(&varsPath, "vars", defaultVarsPath, "defaults role vars file")
	cmd.Flags().StringVar(&defaultsPath, "defaults", defaultDefaultsPath, "defaults role defaults file")
	cmd.Flags().StringVar(&commit, "commit", "", "source commit to record (default: $GITHUB_SHA or git HEAD)")
	cmd.Flags().StringVarP(&output, "output", "o", "", "write the manifest to a file instead of stdout")
	cmd.Flags().BoolVar(&writeVars, "write-vars", false, "also pin the images in the vars file")
	cmd.Flags().StringVar(&resolvePrefix, "resolve-prefix", "", "resolve tags through this pull-through cache prefix first (e.g. harbor.example.com/)")
	return cmd
}

func newWriteVarsCommand(opts *globalOptions) *cobra.Command {
	var varsPath string

	cmd := &cobra.Command{
		Use:   "write-vars MANIFEST",
		Short: "Pin the images in the vars file to a release manifest (file or OCI reference)",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			m, err := opts.load(cmd.Context(), args[0])
			if err != nil {
				return err
			}
			if err := releasemanifest.WriteVars(varsPath, m); err != nil {
				return err
			}
			log.Infof("Pinned images in %s from %s", varsPath, args[0])
			return nil
		},
	}
	cmd.Flags().StringVar(&varsPath, "vars", defaultVarsPath, "defaults role vars file")
	return cmd
}

func newPushCommand(opts *globalOptions) *cobra.Command {
	var file, source string

	cmd := &cobra.Command{
		Use:   "push REFERENCE...",
		Short: "Publish a release manifest file as an OCI artifact",
		Long: `Publish a release manifest file to one repository under every given tag.
References are repository:tag, for example the "tags" output of
docker/metadata-action; empty arguments are ignored.`,
		Example: `  atmosphere-release push --file release-manifest.yaml \
    ghcr.io/vexxhost/atmosphere-release:"$GITHUB_SHA" ghcr.io/vexxhost/atmosphere-release:main`,
		Args: cobra.MinimumNArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			repository, tags, err := releasemanifest.SplitReferences(args)
			if err != nil {
				return err
			}
			data, err := os.ReadFile(file)
			if err != nil {
				return err
			}
			m, err := releasemanifest.Unmarshal(data)
			if err != nil {
				return err
			}
			factory, err := opts.factory()
			if err != nil {
				return err
			}
			repo, err := factory(repository)
			if err != nil {
				return err
			}
			desc, err := releasemanifest.Push(cmd.Context(), repo, m, tags, releasemanifest.PushOptions{Source: source})
			if err != nil {
				return err
			}
			for _, tag := range tags {
				fmt.Printf("%s:%s@%s\n", repository, tag, desc.Digest)
			}
			return nil
		},
	}
	cmd.Flags().StringVarP(&file, "file", "f", releasemanifest.FileName, "manifest file to publish")
	cmd.Flags().StringVar(&source, "source", defaultSource, "source repository annotation")
	return cmd
}

func newDigestCommand() *cobra.Command {
	var file, source string

	cmd := &cobra.Command{
		Use:   "digest",
		Short: "Print the artifact digest that push would publish for a manifest file",
		Long: `Print the digest of the OCI artifact that "push" creates for a manifest
file. Pushes are reproducible, so the same manifest always has the same
digest, wherever it is pushed.`,
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, _ []string) error {
			data, err := os.ReadFile(file)
			if err != nil {
				return err
			}
			m, err := releasemanifest.Unmarshal(data)
			if err != nil {
				return err
			}
			dgst, err := releasemanifest.Digest(cmd.Context(), m, releasemanifest.PushOptions{Source: source})
			if err != nil {
				return err
			}
			fmt.Println(dgst)
			return nil
		},
	}
	cmd.Flags().StringVarP(&file, "file", "f", releasemanifest.FileName, "manifest file")
	cmd.Flags().StringVar(&source, "source", defaultSource, "source repository annotation")
	return cmd
}

func newPublishCommand(opts *globalOptions) *cobra.Command {
	var (
		file, varsPath, defaultsPath, source string
		lookup                               releasemanifest.ZuulLookup
		dryRun                               bool
	)

	cmd := &cobra.Command{
		Use:   "publish REFERENCE...",
		Short: "Publish the release manifest that CI tested for the merged change",
		Long: `Publish the release manifest for a commit. When --change and --patchset
are given, the release manifest generated by the newest Zuul buildset in which
every job passed for that change is published unchanged, as long as it was
generated from the same image inputs as the manifest in --file (or a newly
generated one) for this commit. Otherwise that manifest is published instead
and annotated as untested.`,
		Example: `  atmosphere-release publish --file release-manifest.yaml \
    --zuul-api https://zuul.oss.vexxhost.dev/api --change 4420 --patchset "$HEAD_SHA" \
    ghcr.io/vexxhost/atmosphere-release:"$GITHUB_SHA" ghcr.io/vexxhost/atmosphere-release:main`,
		Args: cobra.MinimumNArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := cmd.Context()
			repository, tags, err := releasemanifest.SplitReferences(args)
			if err != nil {
				return err
			}

			var fallback *releasemanifest.Manifest
			if file != "" {
				data, err := os.ReadFile(file)
				if err != nil {
					return err
				}
				if fallback, err = releasemanifest.Unmarshal(data); err != nil {
					return err
				}
			} else if fallback, err = generate(ctx, varsPath, defaultsPath, "", ""); err != nil {
				return err
			}

			var l *releasemanifest.ZuulLookup
			if lookup.Change != "" {
				if lookup.Patchset == "" || lookup.API == "" {
					return fmt.Errorf("--change needs --patchset and --zuul-api")
				}
				l = &lookup
			}

			// NOTE: The fallback manifest was generated from the source of this
			//       commit, before the vars file may have been pinned in place,
			//       so its inputs are the inputs of this commit.
			inputs := fallback.Inputs
			if inputs == "" {
				return fmt.Errorf("the manifest in %s does not record its image inputs; regenerate it", file)
			}

			d, err := releasemanifest.DecidePublish(ctx, l, inputs, fallback, releasemanifest.PushOptions{Source: source})
			if err != nil {
				return err
			}
			dgst, err := releasemanifest.Digest(ctx, d.Manifest, d.Options)
			if err != nil {
				return err
			}
			if d.Tested != nil {
				log.WithField("digest", dgst).Infof("Publishing the tested release manifest: %s (%s)", d.Reason, d.Tested.URL)
			} else {
				log.WithField("digest", dgst).Warnf("Publishing an untested release manifest: %s", d.Reason)
			}
			if dryRun {
				return nil
			}

			factory, err := opts.factory()
			if err != nil {
				return err
			}
			repo, err := factory(repository)
			if err != nil {
				return err
			}
			desc, err := releasemanifest.Push(ctx, repo, d.Manifest, tags, d.Options)
			if err != nil {
				return err
			}
			for _, tag := range tags {
				fmt.Printf("%s:%s@%s\n", repository, tag, desc.Digest)
			}
			return nil
		},
	}
	cmd.Flags().StringVarP(&file, "file", "f", "", "manifest to publish when no tested manifest is used (default: generate one)")
	cmd.Flags().StringVar(&varsPath, "vars", defaultVarsPath, "defaults role vars file")
	cmd.Flags().StringVar(&defaultsPath, "defaults", defaultDefaultsPath, "defaults role defaults file")
	cmd.Flags().StringVar(&source, "source", defaultSource, "source repository annotation")
	cmd.Flags().StringVar(&lookup.API, "zuul-api", "", "Zuul tenant API URL")
	cmd.Flags().StringVar(&lookup.Project, "zuul-project", "vexxhost/atmosphere", "Zuul project name")
	cmd.Flags().StringVar(&lookup.Change, "change", "", "pull request number that was merged")
	cmd.Flags().StringVar(&lookup.Patchset, "patchset", "", "head commit of the merged pull request")
	cmd.Flags().StringSliceVar(&lookup.Pipelines, "pipeline", []string{"gate", "check"}, "Zuul pipelines to search, in order")
	cmd.Flags().StringVar(&lookup.Job, "zuul-job", releasemanifest.DefaultZuulJob, "Zuul job that generates the manifest")
	cmd.Flags().StringVar(&lookup.Artifact, "zuul-artifact", releasemanifest.DefaultZuulArtifact, "Zuul artifact name of the manifest")
	cmd.Flags().BoolVar(&dryRun, "dry-run", false, "only report which manifest would be published")
	return cmd
}

func newPromoteCommand(opts *globalOptions) *cobra.Command {
	var from, varsPath, defaultsPath, source string
	var generateIfMissing bool

	cmd := &cobra.Command{
		Use:   "promote --from TAG REFERENCE...",
		Short: "Tag an existing release manifest with release tags",
		Long: `Add tags to the manifest published for a commit, without resolving any
image again, so a release ships exactly what CI produced for that commit.
References are repository:tag in one repository, for example the "tags"
output of docker/metadata-action. With --generate-if-missing, a manifest is
generated and pushed for --from first when none exists (for example for
commits made before manifests were published).`,
		Example: `  atmosphere-release promote --from "$GITHUB_SHA" --generate-if-missing \
    ghcr.io/vexxhost/atmosphere-release:v7.9.0`,
		Args: cobra.MinimumNArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := cmd.Context()
			repository, tags, err := releasemanifest.SplitReferences(args)
			if err != nil {
				return err
			}
			factory, err := opts.factory()
			if err != nil {
				return err
			}
			repo, err := factory(repository)
			if err != nil {
				return err
			}

			if _, _, err := releasemanifest.Fetch(ctx, repo, from); err != nil {
				if !errors.Is(err, errdef.ErrNotFound) || !generateIfMissing {
					return err
				}
				log.Warnf("No manifest found for %s:%s, generating one", repository, from)
				m, err := generate(ctx, varsPath, defaultsPath, from, "")
				if err != nil {
					return err
				}
				if _, err := releasemanifest.Push(ctx, repo, m, []string{from}, releasemanifest.PushOptions{Source: source}); err != nil {
					return err
				}
			}

			for _, tag := range tags {
				desc, err := releasemanifest.Promote(ctx, repo, from, tag)
				if err != nil {
					return err
				}
				fmt.Printf("%s:%s@%s\n", repository, tag, desc.Digest)
			}
			return nil
		},
	}
	cmd.Flags().StringVar(&from, "from", "", "existing tag, usually the commit SHA")
	cmd.Flags().BoolVar(&generateIfMissing, "generate-if-missing", false, "generate and push a manifest for --from if none exists")
	cmd.Flags().StringVar(&varsPath, "vars", defaultVarsPath, "defaults role vars file (with --generate-if-missing)")
	cmd.Flags().StringVar(&defaultsPath, "defaults", defaultDefaultsPath, "defaults role defaults file (with --generate-if-missing)")
	cmd.Flags().StringVar(&source, "source", defaultSource, "source repository annotation (with --generate-if-missing)")
	_ = cmd.MarkFlagRequired("from")
	return cmd
}

func newShowCommand(opts *globalOptions) *cobra.Command {
	return &cobra.Command{
		Use:   "show MANIFEST",
		Short: "Print a release manifest (file or OCI reference)",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			m, err := opts.load(cmd.Context(), args[0])
			if err != nil {
				return err
			}
			data, err := m.Marshal()
			if err != nil {
				return err
			}
			_, err = os.Stdout.Write(data)
			return err
		},
	}
}

func newDiffCommand(opts *globalOptions) *cobra.Command {
	return &cobra.Command{
		Use:     "diff FROM TO",
		Short:   "Show the image changes between two release manifests",
		Example: "  atmosphere-release diff ghcr.io/vexxhost/atmosphere-release:v7.8.0 ghcr.io/vexxhost/atmosphere-release:v7.8.1",
		Args:    cobra.ExactArgs(2),
		RunE: func(cmd *cobra.Command, args []string) error {
			a, err := opts.load(cmd.Context(), args[0])
			if err != nil {
				return err
			}
			b, err := opts.load(cmd.Context(), args[1])
			if err != nil {
				return err
			}
			return releasemanifest.WriteDiff(os.Stdout, a, b, releasemanifest.Diff(a, b))
		},
	}
}

type rulesFile struct {
	Mirrors []releasemanifest.MirrorRule `yaml:"atmosphere_image_mirrors"`
}

func readRules(path string) ([]releasemanifest.MirrorRule, error) {
	if path == "" {
		return nil, nil
	}
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var rules rulesFile
	if err := yaml.Unmarshal(data, &rules); err != nil {
		return nil, fmt.Errorf("parsing %s: %w", path, err)
	}
	return rules.Mirrors, nil
}

func newCheckCommand(opts *globalOptions) *cobra.Command {
	var prefix, rulesPath string
	var printImages bool

	cmd := &cobra.Command{
		Use:   "check MANIFEST",
		Short: "Check that a prefix and mirror rules resolve every image of a release",
		Long: `Resolve every image of a release manifest with an image prefix and mirror
rules, the same way a deployment does, and validate the result: every
reference must be valid and the Kubernetes control plane images must stay
under one image repository with their original names.`,
		Example: "  atmosphere-release check ghcr.io/vexxhost/atmosphere-release:v7.8.1 --rules mirror-rules.yml --print",
		Args:    cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			m, err := opts.load(cmd.Context(), args[0])
			if err != nil {
				return err
			}
			rules, err := readRules(rulesPath)
			if err != nil {
				return err
			}
			resolved, err := releasemanifest.ResolveImages(m.Images, releasemanifest.ResolveOptions{Prefix: prefix, Mirrors: rules})
			if err != nil {
				return err
			}
			if printImages {
				data, err := yaml.Marshal(map[string]interface{}{"atmosphere_images": resolved})
				if err != nil {
					return err
				}
				if _, err := os.Stdout.Write(data); err != nil {
					return err
				}
			}
			if errs := releasemanifest.CheckResolved(m, resolved); len(errs) > 0 {
				for _, err := range errs {
					log.Error(err)
				}
				return fmt.Errorf("%d problem(s) found", len(errs))
			}
			log.WithField("images", len(resolved)).Info("All images resolve")
			return nil
		},
	}
	cmd.Flags().StringVar(&prefix, "prefix", "", "atmosphere_image_prefix value")
	cmd.Flags().StringVar(&rulesPath, "rules", "", "YAML file with atmosphere_image_mirrors")
	cmd.Flags().BoolVar(&printImages, "print", false, "print the resolved images")
	return cmd
}

func newMirrorCommand(opts *globalOptions) *cobra.Command {
	var (
		to, toDir, fromDir, layout, kubePrefix, rulesOutput string
		extra                                               []string
	)

	cmd := &cobra.Command{
		Use:   "mirror [MANIFEST]",
		Short: "Copy a release to another registry or to a directory",
		Long: `Copy every image of a release, and the release manifest itself, to a
registry, or export them to a directory for disconnected environments and
import that directory into a registry later.

Images are copied completely (every platform), so their digests do not
change, and every digest is verified after copying. The command writes the
atmosphere_image_mirrors rules that point a deployment at the mirror.

Layouts:
  nested       <to>/quay.io/ceph/ceph       (Harbor, Distribution, Quay with nested repositories)
  flat         <to>/quay.io--ceph--ceph     (registries that limit repository depth, e.g. GitLab)
  single-repo  <to>:quay.io--ceph--ceph--v18.2.7  (registries that only allow one repository)

kubeadm pulls the control plane images by tag from one image repository, so
they keep their original names under --kubernetes-prefix in every layout.
Add the etcd and CoreDNS images kubeadm uses for your Kubernetes version with
--extra-image.`,
		Example: `  # Mirror a release into a registry
  atmosphere-release mirror ghcr.io/vexxhost/atmosphere-release:v7.8.1 \
    --to registry.example.com/atmosphere --rules-output mirror-rules.yml

  # Disconnected: export to a directory, carry it over, then import it
  atmosphere-release mirror ghcr.io/vexxhost/atmosphere-release:v7.8.1 --to-dir /media/atmosphere
  atmosphere-release mirror --from-dir /media/atmosphere --to registry.internal/atmosphere --layout flat`,
		Args: cobra.MaximumNArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := cmd.Context()
			progress := func(format string, a ...interface{}) { log.Infof(format, a...) }

			mopts := releasemanifest.MirrorOptions{
				Destination:      to,
				Layout:           releasemanifest.Layout(layout),
				KubernetesPrefix: kubePrefix,
				ExtraImages:      extra,
			}

			factory, err := opts.factory()
			if err != nil {
				return err
			}

			if fromDir != "" {
				if len(args) > 0 || toDir != "" || to == "" {
					return fmt.Errorf("--from-dir needs --to and no manifest argument")
				}
				plan, err := releasemanifest.Import(ctx, fromDir, mopts, factory, progress)
				if err != nil {
					return err
				}
				return writeMirrorResult(plan, rulesOutput)
			}

			if len(args) != 1 {
				return fmt.Errorf("a release manifest (file or OCI reference) is required")
			}
			m, err := releasemanifest.Load(ctx, args[0], factory)
			if err != nil {
				return err
			}

			var manifestSrc releasemanifest.SourceFunc
			if _, statErr := os.Stat(args[0]); os.IsNotExist(statErr) {
				mopts.ManifestSource = args[0]
				manifestSrc = releasemanifest.RemoteSource(factory)
			}

			src := releasemanifest.RemoteSource(factory)
			switch {
			case toDir != "" && to != "":
				return fmt.Errorf("use either --to or --to-dir")
			case toDir != "":
				if err := releasemanifest.Export(ctx, m, mopts, src, manifestSrc, toDir, progress); err != nil {
					return err
				}
				log.Infof("Exported release to %s", toDir)
				return nil
			case to != "":
				plan, err := releasemanifest.PlanMirror(m, mopts)
				if err != nil {
					return err
				}
				if err := releasemanifest.Mirror(ctx, m, plan, src, manifestSrc, factory, progress); err != nil {
					return err
				}
				return writeMirrorResult(plan, rulesOutput)
			default:
				return fmt.Errorf("either --to or --to-dir is required")
			}
		},
	}
	cmd.Flags().StringVar(&to, "to", "", "destination registry or namespace (repository for single-repo)")
	cmd.Flags().StringVar(&toDir, "to-dir", "", "export to an OCI layout directory")
	cmd.Flags().StringVar(&fromDir, "from-dir", "", "import from a directory written with --to-dir")
	cmd.Flags().StringVar(&layout, "layout", string(releasemanifest.LayoutNested), "mirror layout: nested, flat or single-repo")
	cmd.Flags().StringVar(&kubePrefix, "kubernetes-prefix", "", "image repository for the kubeadm images (required for single-repo)")
	cmd.Flags().StringArrayVar(&extra, "extra-image", nil, "additional image to mirror (repeatable)")
	cmd.Flags().StringVar(&rulesOutput, "rules-output", "", "write the atmosphere_image_mirrors rules to this file")
	return cmd
}

func writeMirrorResult(plan *releasemanifest.MirrorPlan, rulesOutput string) error {
	data, err := yaml.Marshal(rulesFile{Mirrors: plan.Rules})
	if err != nil {
		return err
	}
	header := fmt.Sprintf("# Generated by atmosphere-release mirror.\natmosphere_release_manifest: %s\n", plan.ManifestReference())
	out := append([]byte(header), data...)

	if rulesOutput != "" {
		if err := os.WriteFile(rulesOutput, out, 0o644); err != nil {
			return err
		}
		log.Infof("Wrote mirror rules to %s", rulesOutput)
		return nil
	}
	_, err = os.Stdout.Write(out)
	return err
}
