# Cray Configuration Framework Service Batcher

The cfs-batcher attempts to keep the configuration state of components the same
as the desired configuration state.  All configuration state and desired state
information is stored in the cfs-api database.

Users do not interact directly with the batcher.  It continuously monitors
the state information the cfs has stored, and when it detects components that
do not match the desired configuration state, it schedules CFS sessions.  If
many components need configuration, the batcher will group the components and
schedule multiple sessions as needed to keep the number of components per
session to the desired size.

Because the batcher is constantly checking for components out of the desired
state, it will also retry configuration in cases where it fails.  So long as
the component does not fail to configure more than the maximum number of
retries, the batcher will automatically attempt to re-configure.
