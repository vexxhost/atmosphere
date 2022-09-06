package image_repositories

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"time"

	"github.com/go-git/go-billy/v5"
	"github.com/go-git/go-billy/v5/memfs"
	"github.com/go-git/go-git/v5"
	"github.com/go-git/go-git/v5/config"
	"github.com/go-git/go-git/v5/plumbing"
	"github.com/go-git/go-git/v5/plumbing/object"
	git_http "github.com/go-git/go-git/v5/plumbing/transport/http"
	"github.com/go-git/go-git/v5/storage/memory"
	"github.com/google/go-github/v47/github"
	log "github.com/sirupsen/logrus"
	"golang.org/x/oauth2"
)

type ImageRepository struct {
	Project string

	githubClient      *github.Client
	githubProjectName string
	gitAuth           *git_http.BasicAuth
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

		githubClient:      github.NewClient(tc),
		githubProjectName: fmt.Sprintf("docker-openstack-%s", project),
		gitAuth: &git_http.BasicAuth{
			Username: "x-access-token",
			Password: githubToken,
		},
	}
}

func (i *ImageRepository) WriteFiles(ctx context.Context, fs billy.Filesystem) error {
	// .github/workflows/build.yml
	build := NewBuildWorkflow(i.Project)
	err := build.WriteFile(fs)
	if err != nil {
		return err
	}

	// .github/workflows/sync.yml
	sync := NewSyncWorkflow(i.Project)
	err = sync.WriteFile(fs)
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
	df, err := NewDockerfile(ctx, i)
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

func (i *ImageRepository) CreateGithubRepository(ctx context.Context) error {
	repo := &github.Repository{
		Name:     github.String(i.githubProjectName),
		AutoInit: github.Bool(true),
	}

	_, _, err := i.githubClient.Repositories.Create(ctx, "vexxhost", repo)
	if err != nil {
		return err
	}

	return nil
}

func (i *ImageRepository) GetGitHubRepository(ctx context.Context, owner string) (*github.Repository, error) {
	repo, _, err := i.githubClient.Repositories.Get(ctx, owner, i.githubProjectName)
	if err != nil {
		return nil, err
	}

	return repo, nil
}

func (i *ImageRepository) ForkGitHubRepository(ctx context.Context) (*github.Repository, error) {
	repo, err := i.GetGitHubRepository(ctx, "vexxhost-bot")
	if err != nil {
		i.githubClient.Repositories.CreateFork(ctx, "vexxhost", i.githubProjectName, nil)
		time.Sleep(20 * time.Second)
		return i.GetGitHubRepository(ctx, "vexxhost-bot")
	}

	return repo, nil
}

func (i *ImageRepository) UpdateGithubConfiguration(ctx context.Context) error {
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
	repo, _, err := i.githubClient.Repositories.Edit(ctx, "vexxhost", i.githubProjectName, repo)
	if err != nil {
		return err
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
		EnforceAdmins:                  false,
		AllowForcePushes:               github.Bool(false),
		AllowDeletions:                 github.Bool(false),
	}
	_, _, err = i.githubClient.Repositories.UpdateBranchProtection(ctx, *repo.Owner.Login, *repo.Name, "main", protection)
	if err != nil {
		return err
	}

	return nil
}

func (i *ImageRepository) Synchronize(ctx context.Context, admin bool) error {
	var githubRepo *github.Repository
	var err error

	if admin {
		githubRepo, err = i.GetGitHubRepository(ctx, "vexxhost")
	} else {
		githubRepo, err = i.ForkGitHubRepository(ctx)
	}

	if err != nil {
		return err
	}

	storer := memory.NewStorage()
	fs := memfs.New()

	upstreamUrl := fmt.Sprintf("https://github.com/vexxhost/%s.git", i.githubProjectName)
	repo, err := git.Clone(storer, fs, &git.CloneOptions{
		Auth:       i.gitAuth,
		URL:        upstreamUrl,
		RemoteName: "upstream",
	})
	if err != nil {
		return err
	}

	_, err = repo.CreateRemote(&config.RemoteConfig{
		Name: "origin",
		URLs: []string{*githubRepo.CloneURL},
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

	err = i.WriteFiles(ctx, fs)
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
		Author: &object.Signature{
			Name:  "vexxhost-bot",
			Email: "mnaser+bot@vexxhost.com",
			When:  time.Now(),
		},
	})
	if err != nil {
		return err
	}

	err = repo.Push(&git.PushOptions{
		Auth:       i.gitAuth,
		RefSpecs:   []config.RefSpec{"refs/heads/*:refs/heads/*"},
		RemoteName: "origin",
		Force:      true,
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
	head := fmt.Sprintf("%s:%s", *repo.Owner.Login, "sync/atmosphere-ci")

	newPR := &github.NewPullRequest{
		Title: github.String("⚙️ Automatic sync from `atmosphere-ci`"),
		Head:  github.String(head),
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

	pr, resp, err := i.githubClient.PullRequests.Create(ctx, "vexxhost", *repo.Name, newPR)
	if err != nil && resp.StatusCode != http.StatusUnprocessableEntity {
		return err
	}

	log.Info("PR created: ", pr.GetHTMLURL())
	return nil
}
