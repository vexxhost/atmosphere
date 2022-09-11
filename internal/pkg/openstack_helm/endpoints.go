package openstack_helm

type Endpoints struct {
}

type Endpoint struct {
}

func NewEndpointValues() *EndpointValues {
	return &EndpointValues{
		Endpoints: &Endpoints{},
	}
}
