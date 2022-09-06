package image_repositories

import (
	"context"
	"fmt"
	"net/http"
	"os"

	"github.com/go-git/go-billy/v5"
	"github.com/go-git/go-billy/v5/memfs"
	"github.com/go-git/go-git/v5"
	"github.com/go-git/go-git/v5/config"
	"github.com/go-git/go-git/v5/plumbing"
	git_http "github.com/go-git/go-git/v5/plumbing/transport/http"
	"github.com/go-git/go-git/v5/storage/memory"
	"github.com/google/go-github/v47/github"
	log "github.com/sirupsen/logrus"
	"golang.org/x/oauth2"
)

type ImageRepository struct {
	Project string

	githubClient *github.Client
	gitAuth      *git_http.BasicAuth
}

func NewImageRepository(project string) *ImageRepository {
	githubToken := os.Getenv("GITHUB_TOKEN")

	ctx := context.TODO()
	ts := oauth2.StaticTokenSource(
		&oauth2.Token{AccessToken: os.Getenv("GITHUB_TOKEN")},
	)
	tc := oauth2.NewClient(ctx, ts)

	return &ImageRepository{
		Project: project,

		githubClient: github.NewClient(tc),
		gitAuth: &git_http.BasicAuth{
			Username: githubToken,
		},
	}
}

func (i *ImageRepository) WriteFiles(fs billy.Filesystem) error {
	// .github/workflows/build.yml
	build := NewBuildWorkflow(i.Project)
	err := build.WriteFile(fs)
	if err != nil {
		return err
	}

	// .github/workflows/sync.yml

	// .github/dependabot.yml
	dab := NewDependabotConfig()
	err = dab.WriteFile(fs)
	if err != nil {
		return err
	}

	// .dockerignore
	di := NewDockerIgnore()
	err = di.WriteFile(fs)
	if err != nil {
		return err
	}

	// .pre-commit-config.yaml
	pcc := NewPreCommitConfig()
	err = pcc.WriteFile(fs)
	if err != nil {
		return err
	}

	// Dockerfile
	df, err := NewDockerfile()
	if err != nil {
		return err
	}
	err = df.WriteFile(fs)
	if err != nil {
		return err
	}

	// manifest.yml
	mf, err := NewImageManifest(i.Project)
	if err != nil {
		return err
	}
	err = mf.WriteFile(fs)
	if err != nil {
		return err
	}

	// README.md
	rm, err := NewReadme(i.Project)
	if err != nil {
		return err
	}
	err = rm.WriteFile(fs)
	if err != nil {
		return err
	}

	return nil
}

func (i *ImageRepository) CreateOrGet(ctx context.Context) (*github.Repository, error) {
	projectName := fmt.Sprintf("docker-openstack-%s", i.Project)

	_, resp, err := i.githubClient.Repositories.Get(ctx, "vexxhost", projectName)
	if err != nil && resp.StatusCode == http.StatusNotFound {
		_, _, err = i.githubClient.Repositories.Create(ctx, "vexxhost", &github.Repository{
			Name: github.String(projectName),
		})
		if err != nil {
			return nil, err
		}
	}

	// Description
	description := fmt.Sprintf("Docker image for OpenStack: %s", i.Project)

	// Updated repository
	repo := &github.Repository{
		AllowMergeCommit:    github.Bool(false),
		AllowRebaseMerge:    github.Bool(true),
		AllowSquashMerge:    github.Bool(false),
		DeleteBranchOnMerge: github.Bool(true),
		Description:         github.String(description),
		Visibility:          github.String("public"),
		HasWiki:             github.Bool(false),
		HasIssues:           github.Bool(false),
		HasProjects:         github.Bool(false),
	}

	// Update the repository with the correct settings
	repo, _, err = i.githubClient.Repositories.Edit(ctx, "vexxhost", projectName, repo)
	if err != nil {
		return nil, err
	}

	// Branch protection
	protection := &github.ProtectionRequest{
		RequiredPullRequestReviews: &github.PullRequestReviewsEnforcementRequest{
			RequiredApprovingReviewCount: 1,
			DismissStaleReviews:          true,
			BypassPullRequestAllowancesRequest: &github.BypassPullRequestAllowancesRequest{
				Users: []string{"mnaser"},
				Teams: []string{},
				Apps:  []string{},
			},
		},
		RequiredStatusChecks: &github.RequiredStatusChecks{
			Strict:   true,
			Contexts: nil,
			Checks: []*github.RequiredStatusCheck{
				{
					Context: "image (wallaby)",
				},
				{
					Context: "image (xena)",
				},
				{
					Context: "image (yoga)",
				},
			},
		},
		RequiredConversationResolution: github.Bool(true),
		RequireLinearHistory:           github.Bool(true),
		EnforceAdmins:                  true,
		AllowForcePushes:               github.Bool(false),
		AllowDeletions:                 github.Bool(false),
	}
	_, _, err = i.githubClient.Repositories.UpdateBranchProtection(ctx, *repo.Owner.Login, *repo.Name, "main", protection)
	if err != nil {
		return nil, err
	}

	return repo, err
}

func (i *ImageRepository) Synchronize(ctx context.Context) error {
	githubRepo, err := i.CreateOrGet(ctx)
	if err != nil {
		return err
	}

	storer := memory.NewStorage()
	fs := memfs.New()

	repo, err := git.Clone(storer, fs, &git.CloneOptions{
		Auth: i.gitAuth,
		URL:  *githubRepo.SSHURL,
	})
	if err != nil {
		return err
	}

	headRef, err := repo.Head()
	if err != nil {
		return err
	}

	ref := plumbing.NewHashReference("refs/heads/sync/atmosphere-ci", headRef.Hash())
	err = repo.Storer.SetReference(ref)
	if err != nil {
		return err
	}

	worktree, err := repo.Worktree()
	if err != nil {
		return err
	}

	err = worktree.Checkout(&git.CheckoutOptions{
		Branch: ref.Name(),
	})
	if err != nil {
		return err
	}

	err = i.WriteFiles(fs)
	if err != nil {
		return err
	}

	status, err := worktree.Status()
	if err != nil {
		return err
	}

	if status.IsClean() {
		log.Info("No changes to commit")
		return nil
	}

	_, err = worktree.Add(".")
	if err != nil {
		return err
	}

	commit, err := worktree.Commit("chore: sync using `atmosphere-ci`", &git.CommitOptions{
		All: true,
	})
	if err != nil {
		return err
	}

	err = repo.Push(&git.PushOptions{
		Auth:     i.gitAuth,
		RefSpecs: []config.RefSpec{"refs/heads/sync/atmosphere-ci:refs/heads/sync/atmosphere-ci"},
		Force:    true,
	})
	if err != nil {
		return err
	}

	err = i.CreatePullRequest(ctx, githubRepo, commit)
	if err != nil {
		return err
	}

	return nil
}

func (i *ImageRepository) CreatePullRequest(ctx context.Context, repo *github.Repository, commit plumbing.Hash) error {
	newPR := &github.NewPullRequest{
		Title: github.String("⚙️ Automatic sync from `atmosphere-ci`"),
		Head:  github.String("sync/atmosphere-ci"),
		Base:  github.String("main"),
		Body:  github.String("This is an automatic pull request from `atmosphere-ci`"),
	}

	prs, _, err := i.githubClient.PullRequests.ListPullRequestsWithCommit(ctx, *repo.Owner.Login, *repo.Name, commit.String(), &github.PullRequestListOptions{})
	if err != nil {
		return err
	}

	if len(prs) > 0 {
		log.Info("Pull request already exists: ", prs[0].GetHTMLURL())
		return nil
	}

	pr, resp, err := i.githubClient.PullRequests.Create(ctx, *repo.Owner.Login, *repo.Name, newPR)
	if err != nil && resp.StatusCode != http.StatusUnprocessableEntity {
		return err
	}

	log.Info("PR created: ", pr.GetHTMLURL())
	return nil
}
